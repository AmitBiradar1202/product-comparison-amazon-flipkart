import requests
import re
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from textblob import TextBlob
from config import API_KEY, SEARCH_ENGINE_ID, CHROME_DRIVER_PATH

# Lock to allow only one search at a time

API_KEY = "Get Your Own"
SEARCH_ENGINE_ID = "Get Your Own"

# Setup Selenium WebDriver (Update path as per your system)
CHROME_DRIVER_PATH = "C:\\chromedriver-win64\\chromedriver.exe"

# Lock to allow only one search at a time
search_lock = threading.Lock()

def search_product(product_name):
    """Fetches top 10 product search results from Google Custom Search API."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": product_name,
        "key": API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "num": 10
    }
    response = requests.get(url, params=params)
    data = response.json()
    results = {}
    
    if "items" in data:
        for item in data["items"]:
            link = item.get("link", "")
            if "amazon.in" in link:
                results["amazon"] = link
            elif "flipkart.com" in link:
                results["flipkart"] = link
            
            if "amazon" in results and "flipkart" in results:
                break  # Stop when both links are found
    
    return results

def get_webdriver():
    """Configure and return a Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36")
    
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_flipkart(product_url):
    """Scrapes Flipkart product details."""
    driver = get_webdriver()
    
    try:
        driver.get(product_url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        try:
            product_name = soup.find("span", class_="VU-ZEz").text.strip()
        except:
            product_name = "Product name not found"
        
        price = "Price not found"
        for price_class in ["yiggsN", "Nx9bqj CxhGGd", "Nx9bqj CxhGGd yKS4la"]:
            price_tags = soup.find_all("div", class_=price_class)
            for tag in price_tags:
                text = tag.text.strip()
                
                # Skip unwanted non-price texts
                if "Enter pincode" in text or not re.search(r'₹\d[\d,]*', text):
                    continue
                
                # If it says /month, fetch actual price from best class
                if "/month" in text:
                    actual_price_tag = soup.find("div", class_="Nx9bqj CxhGGd yKS4la")
                    if actual_price_tag:
                        price = actual_price_tag.text.strip()
                    else:
                        price = text
                else:
                    price = text
                break  # found a valid price, exit inner loop
            if price != "Price not found":
                break  # valid price found, exit outer loop
        
        # Extract image
        image_tag = soup.find("img", class_="DByuf4 IZexXJ jLEJ7H")
        image_url = image_tag['src'] if image_tag else "Image not found"
        
        # Extract delivery information
        try:
            # Try to find delivery details with various selectors
            delivery_info = "Delivery info not found"
            
            # First attempt - standard layout
            delivery_elem = soup.find("div", class_="hVvnXm")
            if delivery_elem:
                date_span = delivery_elem.find("span", class_="Y8v7Fl")
                if date_span:
                    delivery_date = date_span.text.strip()
                    
                    # Try to find delivery condition
                    condition_elem = soup.find("div", class_="m-cM89")
                    delivery_condition = condition_elem.text.strip() if condition_elem else ""
                    
                    if delivery_condition:
                        delivery_info = f"{delivery_date} ({delivery_condition})"
                    else:
                        delivery_info = delivery_date
            
            # Second attempt - alternative layout
            if delivery_info == "Delivery info not found":
                delivery_elements = soup.find_all(["div", "span"], string=re.compile(r'Delivery by|Expected Delivery|Get it by', re.I))
                if delivery_elements:
                    for elem in delivery_elements:
                        # Get parent text which often contains the full delivery information
                        parent_text = elem.parent.get_text(strip=True)
                        if re.search(r'(Delivery|Get it) by', parent_text, re.I):
                            delivery_info = parent_text
                            break
        except Exception as e:
            print(f"Error extracting Flipkart delivery: {e}")
            delivery_info = "Delivery info not found"
        
        # Extract rating
        try:
            rating_tag = soup.find("div", class_="ipqd2A")
            rating = float(rating_tag.text.strip()) if rating_tag else 0.0
        except:
            rating = 0.0
        
        # Extract reviews
        reviews = [rev.text.strip().split("READ MORE")[0] for rev in soup.find_all("div", class_="ZmyHeo")[:5]]
        sentiment = analyze_sentiment(" ".join(reviews))
        
        return {
            "name": product_name, 
            "price": price, 
            "rating": rating, 
            "sentiment": sentiment,
            "image": image_url,
            "reviews": reviews,
            "delivery": delivery_info,
            "Flipkart_URL": product_url
        }
    
    finally:
        driver.quit()

def scrape_amazon(product_url):
    """Scrapes Amazon product details."""
    driver = get_webdriver()
    
    try:
        driver.get(product_url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        try:
            product_name = soup.find("span", {"id": "productTitle"}).text.strip()
        except:
            product_name = "Product name not found"
        
        try:
            price = soup.find("span", class_="a-price-whole").text.strip()
            price = f"₹{int(re.sub(r'[^0-9]', '', price))}"  # Extract only numeric part
        except:
            price = "Price not found"
        
        try:
            rating = soup.find("span", {"data-hook": "rating-out-of-text"}).text.strip()
            rating = float(rating.split()[0])
        except:
            rating = 0.0
            
        # Extract delivery information
        try:
            delivery_info = "Delivery info not found"
            
            # First attempt - look for specific delivery text
            delivery_spans = soup.find_all("span", class_="a-text-bold")
            for span in delivery_spans:
                text = span.get_text(strip=True)
                if any(month in text for month in ["January", "February", "March", "April", "May", "June", 
                                                "July", "August", "September", "October", "November", "December"]):
                    delivery_info = text
                    break
            
            # Second attempt - look for delivery date section
            if delivery_info == "Delivery info not found":
                # Look for "FREE Delivery" or "Get it by" sections
                delivery_elems = soup.find_all(["span", "div"], string=re.compile(r'FREE Delivery|Get it by|Delivery by', re.I))
                for elem in delivery_elems:
                    parent = elem.parent
                    parent_text = parent.get_text(strip=True)
                    
                    # Look for dates in the parent text
                    date_match = re.search(r'(today|tomorrow|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))', 
                                         parent_text, re.I)
                    if date_match:
                        # Find the full delivery text
                        if "fastest delivery" in parent_text.lower():
                            delivery_info = f"Fast Delivery: {date_match.group(0)}"
                        else:
                            delivery_info = f"Delivery by {date_match.group(0)}"
                        break
                    
            # Third attempt - check for shipping message area
            if delivery_info == "Delivery info not found":
                delivery_section = soup.find(id="deliveryBlockMessage")
                if delivery_section:
                    delivery_text = delivery_section.get_text(strip=True)
                    # Extract a reasonable portion of text with date information
                    date_match = re.search(r'(Delivery|Get it|Ships).{1,50}(today|tomorrow|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))', 
                                         delivery_text, re.I)
                    if date_match:
                        delivery_info = date_match.group(0)
        
        except Exception as e:
            print(f"Error extracting Amazon delivery: {e}")
            delivery_info = "Delivery info not found"

        # Extract image from Amazon
        image_tag = soup.find("img", id="landingImage")
        image_url = image_tag.get("data-old-hires") or image_tag.get("src") if image_tag else "Image not fopound"
            
        reviews = [rev.find("span").text.strip() for rev in soup.find_all("div", {"data-hook": "review-collapsed"})[:5]]
        sentiment = analyze_sentiment(" ".join(reviews))
        
        return {
            "name": product_name, 
            "price": price, 
            "rating": rating, 
            "sentiment": sentiment,
            "image": image_url,
            "reviews": reviews,
            "delivery": delivery_info,
            "Amazon_URL": product_url
        }
    
    finally:
        driver.quit()

def analyze_sentiment(text):
    """Performs sentiment analysis on reviews."""
    if not text:
        return 0.0
    return TextBlob(text).sentiment.polarity
