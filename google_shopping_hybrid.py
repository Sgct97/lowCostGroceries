"""
HYBRID Google Shopping Scraper
- Uses Playwright ONCE to capture the callback endpoint
- Then uses requests for all subsequent calls (fast!)
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright
import time

class ProductParser:
    """Parse product data from HTML"""
    
    @staticmethod
    def parse_products(html: str) -> List[Dict]:
        """Extract all products from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Find product containers
        containers = soup.find_all('div', class_='liKJmf')
        
        for container in containers:
            try:
                product = ProductParser.parse_single_product(container)
                if product.get('title') and product.get('price'):
                    products.append(product)
            except Exception as e:
                continue
        
        return products
    
    @staticmethod
    def parse_single_product(container) -> Dict:
        """Parse a single product container"""
        soup = BeautifulSoup(str(container), 'html.parser')
        
        # Title
        title_elem = soup.find('div', class_='gkQHve')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Price
        price = None
        price_elem = soup.find('span', class_='lmQWe')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if match:
                price = float(match.group(1).replace(',', ''))
        
        # Original price
        original_price = None
        was_price = soup.find('span', class_='DoCHT')
        if was_price:
            price_text = was_price.get_text(strip=True)
            match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if match:
                original_price = float(match.group(1).replace(',', ''))
        
        # Merchant
        merchant_elem = soup.find('span', class_='WJMUdc')
        merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
        
        # Rating
        rating = None
        rating_elem = soup.find('span', class_='yi40Hd')
        if rating_elem:
            try:
                rating = float(rating_elem.get_text(strip=True))
            except ValueError:
                pass
        
        # Review count
        reviews = None
        reviews_elem = soup.find('span', class_='RDApEe')
        if reviews_elem:
            text = reviews_elem.get_text(strip=True)
            match = re.search(r'\(([0-9.]+)([KM])?\)', text)
            if match:
                num = float(match.group(1))
                multiplier = match.group(2)
                if multiplier == 'K':
                    num *= 1000
                elif multiplier == 'M':
                    num *= 1000000
                reviews = int(num)
        
        # Image
        image_url = None
        img = soup.find('img', class_='VeBrne')
        if img:
            image_url = img.get('data-src') or img.get('src')
            if image_url and image_url.startswith('data:'):
                image_url = None
        
        # Product ID
        product_id = None
        parent = soup.find('div', {'data-iid': True})
        if parent:
            product_id = parent.get('data-iid')
        
        return {
            'title': title,
            'price': price,
            'original_price': original_price,
            'merchant': merchant,
            'rating': rating,
            'review_count': reviews,
            'image_url': image_url,
            'product_id': product_id
        }


class GoogleShoppingHybridScraper:
    """Hybrid scraper - Playwright for endpoint capture, requests for data"""
    
    def __init__(self):
        self.callback_url_template = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
    
    def capture_callback_endpoint(self, query: str = "milk") -> Optional[str]:
        """
        Use Playwright to load the page and capture the callback endpoint
        This is done ONCE to discover the pattern
        """
        print(f"🎯 Capturing callback endpoint for query: '{query}'")
        
        captured_url = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Capture XHR requests
            all_requests = []
            
            def handle_request(request):
                nonlocal captured_url
                url = request.url
                all_requests.append(url)
                
                # Look for the callback endpoint
                if '/async/callback' in url and 'fc=' in url:
                    print(f"   ✅ CAPTURED: {url[:100]}...")
                    captured_url = url
                # Debug: Show other async endpoints
                elif '/async/' in url or '/shopping/' in url:
                    print(f"   🔍 Found: {url[:80]}...")
            
            page.on('request', handle_request)
            
            # Load Google Shopping
            print(f"   → Loading shopping.google.com...")
            page.goto(f'https://shopping.google.com/search?q={query}', wait_until='networkidle')
            
            # Wait for XHR to complete
            print(f"   → Waiting for data load...")
            time.sleep(5)  # Give time for async requests
            
            browser.close()
        
        return captured_url
    
    def fetch_products_from_url(self, url: str) -> str:
        """Fetch product data using the captured URL with requests (FAST!)"""
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        
        content = response.text
        
        # Remove XSSI protection
        if content.startswith(')]}\''):
            content = content[4:]
        
        return content
    
    def search(self, query: str) -> List[Dict]:
        """
        Search Google Shopping
        
        Args:
            query: Search term (e.g., "oat milk", "eggs")
        
        Returns:
            List of product dictionaries
        """
        print(f"\n{'='*80}")
        print(f"🔍 SEARCHING: {query}")
        print(f"{'='*80}")
        
        # Step 1: Capture the callback endpoint
        callback_url = self.capture_callback_endpoint(query)
        
        if not callback_url:
            print("❌ Failed to capture callback endpoint")
            return []
        
        # Step 2: Fetch data using requests (FAST!)
        print(f"\n   → Fetching product data with requests...")
        html = self.fetch_products_from_url(callback_url)
        
        print(f"   → Received {len(html):,} bytes")
        
        # Step 3: Parse products
        print(f"   → Parsing products...")
        products = ProductParser.parse_products(html)
        
        print(f"   ✅ Found {len(products)} products")
        
        return products


def main():
    """Demo the hybrid scraper"""
    
    scraper = GoogleShoppingHybridScraper()
    
    # Search for milk
    products = scraper.search("milk")
    
    print("\n" + "="*80)
    print("📦 PRODUCTS FOUND:")
    print("="*80)
    
    for i, product in enumerate(products[:15], 1):
        print(f"\n{i}. {product['title']}")
        print(f"   💰 ${product['price']}", end="")
        
        if product['original_price']:
            savings = product['original_price'] - product['price']
            pct = (savings / product['original_price']) * 100
            print(f" (was ${product['original_price']} - SAVE {pct:.0f}%!)", end="")
        
        print(f"\n   🏪 {product['merchant']}")
        
        if product['rating']:
            stars = "⭐" * int(round(product['rating']))
            print(f"   {stars} {product['rating']}/5 ({product['review_count']:,} reviews)")
    
    print("\n" + "="*80)
    print(f"✅ Total: {len(products)} products found")
    print("="*80)
    
    # Save to JSON
    output_file = '/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/products.json'
    with open(output_file, 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"\n💾 Saved to: products.json")


if __name__ == "__main__":
    main()

