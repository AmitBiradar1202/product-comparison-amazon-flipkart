/**
 * Main JavaScript file for PriceMatch application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Function to format price numbers with commas and currency symbol
    window.formatPrice = function(price) {
        if (!price) return "₹0";
        
        // Remove any existing currency symbol and commas
        let numericPrice = price.toString().replace(/[₹,]/g, '');
        
        // Add commas as thousands separators
        numericPrice = parseInt(numericPrice).toLocaleString('en-IN');
        
        // Add currency symbol
        return `₹${numericPrice}`;
    };
    
    // Function to handle search form validation
    const searchForms = document.querySelectorAll('form[data-search]');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[type="text"]');
            
            if (!searchInput.value.trim()) {
                e.preventDefault();
                
                // Shake animation for empty input
                searchInput.classList.add('is-invalid');
                setTimeout(() => {
                    searchInput.classList.remove('is-invalid');
                }, 500);
            }
        });
    });
    
    // Function to show back to top button on scroll
    window.addEventListener('scroll', function() {
        const backToTopBtn = document.getElementById('back-to-top');
        if (backToTopBtn) {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        }
    });
});
