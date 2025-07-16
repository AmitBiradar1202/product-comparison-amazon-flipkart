import os
import json
from flask import Flask, render_template, request, jsonify
from utils import search_product, scrape_amazon, scrape_flipkart

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

@app.route('/')
def index():
    """Home page route."""
    return render_template('index.html')

@app.route('/compare', methods=['POST'])
def compare():
    """Compare products from Amazon and Flipkart."""
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        if not product_name:
            return jsonify({'error': 'Product name is required'}), 400
            
        try:
            # Search for product links
            links = search_product(product_name)
            
            if "amazon" not in links or "flipkart" not in links:
                return jsonify({
                    'error': 'Product not found on one or both platforms',
                    'amazon_found': "amazon" in links,
                    'flipkart_found': "flipkart" in links
                }), 404
                
            # Scrape details from both platforms
            amazon_data = scrape_amazon(links["amazon"])
            flipkart_data = scrape_flipkart(links["flipkart"])
            
            # Compare products
            comparison_result = compare_products(amazon_data, flipkart_data)
            
            # Prepare response
            response = {
                'amazon': amazon_data,
                'flipkart': flipkart_data,
                'comparison': comparison_result
            }
            
            return jsonify(response)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
@app.route('/comparison')
def comparison_page():
    """Render the comparison page."""
    product_name = request.args.get('product_name', '')
    return render_template('comparison.html', product_name=product_name)

def compare_products(amazon_data, flipkart_data):
    """Compare products and determine the best choice."""
    import re
    
    # Extract numerical prices
    def extract_price(price_str):
        match = re.search(r'₹([\d,]*)', price_str)
        return int(match.group(1).replace(",", "")) if match else float('inf')
    
    try:
        amazon_price = extract_price(amazon_data['price'])
        flipkart_price = extract_price(flipkart_data['price'])
        
        # Sentiment comparison
        amazon_sentiment = amazon_data['sentiment']
        flipkart_sentiment = flipkart_data['sentiment']
        
        # Get delivery information
        amazon_delivery = amazon_data.get('delivery', 'Delivery info not found')
        flipkart_delivery = flipkart_data.get('delivery', 'Delivery info not found')
        
        # Determine if one has significantly faster delivery
        faster_delivery = None
        if "not found" not in amazon_delivery and "not found" not in flipkart_delivery:
            # This is a simple check - in a real app, you'd parse the dates and calculate differences
            if "same day" in amazon_delivery.lower() or "today" in amazon_delivery.lower():
                faster_delivery = "Amazon"
            elif "same day" in flipkart_delivery.lower() or "today" in flipkart_delivery.lower():
                faster_delivery = "Flipkart"
        
        # Both sentiment and price comparison with delivery consideration
        if amazon_sentiment > flipkart_sentiment and amazon_price <= flipkart_price:
            best_choice = "Amazon"
            reason = "Better reviews and lower price"
            if faster_delivery == "Amazon":
                reason += " with faster delivery"
        elif flipkart_sentiment > amazon_sentiment and flipkart_price <= amazon_price:
            best_choice = "Flipkart"
            reason = "Better reviews and lower price"
            if faster_delivery == "Flipkart":
                reason += " with faster delivery"
        elif amazon_sentiment > flipkart_sentiment:
            best_choice = "Amazon"
            reason = "Better reviews, but higher price"
            if faster_delivery == "Amazon":
                reason += " with faster delivery"
        elif flipkart_sentiment > amazon_sentiment:
            best_choice = "Flipkart"
            reason = "Better reviews, but higher price"
            if faster_delivery == "Flipkart":
                reason += " with faster delivery"
        elif amazon_price < flipkart_price:
            best_choice = "Amazon"
            reason = "Cheaper, reviews are similar"
            if faster_delivery == "Amazon":
                reason += " with faster delivery"
            elif faster_delivery == "Flipkart":
                reason += ", but Flipkart has faster delivery"
        elif flipkart_price < amazon_price:
            best_choice = "Flipkart"
            reason = "Cheaper, reviews are similar"
            if faster_delivery == "Flipkart":
                reason += " with faster delivery"
            elif faster_delivery == "Amazon":
                reason += ", but Amazon has faster delivery"
        else:
            best_choice = "Both are equal"
            reason = "Same price and similar reviews"
            if faster_delivery:
                reason += f", but {faster_delivery} has faster delivery"
        
        return {
            'best_choice': best_choice,
            'reason': reason,
            'price_difference': abs(amazon_price - flipkart_price),
            'amazon_price': amazon_price,
            'flipkart_price': flipkart_price,
            'amazon_sentiment': 'Positive' if amazon_sentiment > 0 else 'Negative' if amazon_sentiment < 0 else 'Neutral',
            'flipkart_sentiment': 'Positive' if flipkart_sentiment > 0 else 'Negative' if flipkart_sentiment < 0 else 'Neutral',
            'amazon_delivery': amazon_delivery,
            'flipkart_delivery': flipkart_delivery
        }
    except Exception as e:
        return {
            'best_choice': 'Could not determine',
            'reason': f'Error comparing products: {str(e)}',
            'price_difference': 0
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
