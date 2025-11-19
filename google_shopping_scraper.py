"""
Google Shopping Scraper
Uses the /async/callback endpoint to get product data
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import List, Dict, Optional
from urllib.parse import urlencode

class GoogleShoppingProduct:
    """Represents a single product from Google Shopping"""
    
    def __init__(self, html_element):
        self.soup = BeautifulSoup(str(html_element), 'html.parser')
        
    def get_title(self) -> Optional[str]:
        """Extract product title"""
        title = self.soup.find('div', class_='gkQHve')
        return title.get_text(strip=True) if title else None
    
    def get_price(self) -> Optional[float]:
        """Extract current price"""
        price_elem = self.soup.find('span', class_='lmQWe')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Extract number from $XX.XX format
            match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if match:
                return float(match.group(1).replace(',', ''))
        return None
    
    def get_original_price(self) -> Optional[float]:
        """Extract original/was price if on sale"""
        was_price = self.soup.find('span', class_='DoCHT')
        if was_price:
            price_text = was_price.get_text(strip=True)
            match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if match:
                return float(match.group(1).replace(',', ''))
        return None
    
    def get_merchant(self) -> Optional[str]:
        """Extract merchant/store name"""
        merchant = self.soup.find('span', class_='WJMUdc')
        return merchant.get_text(strip=True) if merchant else None
    
    def get_rating(self) -> Optional[float]:
        """Extract product rating"""
        rating = self.soup.find('span', class_='yi40Hd')
        if rating:
            try:
                return float(rating.get_text(strip=True))
            except ValueError:
                return None
        return None
    
    def get_review_count(self) -> Optional[int]:
        """Extract number of reviews"""
        reviews = self.soup.find('span', class_='RDApEe')
        if reviews:
            text = reviews.get_text(strip=True)
            # Extract number from (XX) or (X.XK) format
            match = re.search(r'\(([0-9.]+)([KM])?\)', text)
            if match:
                num = float(match.group(1))
                multiplier = match.group(2)
                if multiplier == 'K':
                    num *= 1000
                elif multiplier == 'M':
                    num *= 1000000
                return int(num)
        return None
    
    def get_image_url(self) -> Optional[str]:
        """Extract product image URL"""
        img = self.soup.find('img', class_='VeBrne')
        if img:
            # Check data-src first (lazy loaded)
            if img.get('data-src'):
                return img.get('data-src')
            # Fallback to src
            src = img.get('src')
            if src and not src.startswith('data:'):
                return src
        return None
    
    def get_product_id(self) -> Optional[str]:
        """Extract product/data ID"""
        parent = self.soup.find('div', {'data-iid': True})
        if parent:
            return parent.get('data-iid')
        return None
    
    def to_dict(self) -> Dict:
        """Convert product to dictionary"""
        return {
            'title': self.get_title(),
            'price': self.get_price(),
            'original_price': self.get_original_price(),
            'merchant': self.get_merchant(),
            'rating': self.get_rating(),
            'review_count': self.get_review_count(),
            'image_url': self.get_image_url(),
            'product_id': self.get_product_id()
        }


class GoogleShoppingScraper:
    """
    Scrapes Google Shopping using the /async/callback endpoint
    
    TWO MODES:
    1. AUTO MODE: Tries to extract callback URL automatically (may get blocked)
    2. MANUAL MODE: You provide a callback URL from your browser (FAST & RELIABLE)
    
    To get a callback URL:
    1. Open Chrome DevTools → Network tab
    2. Go to https://www.google.com/search?q=milk&tbm=shop  
    3. Look for /async/callback request
    4. Right-click → Copy → Copy URL
    5. Pass it to search_with_callback_url()
    """
    
    def __init__(self):
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
        self.callback_url_template = None
    
    def get_initial_page(self, query: str) -> str:
        """
        Load initial Google Shopping page to trigger the callback
        Google will redirect and make the callback request
        """
        url = "https://www.google.com/search"
        params = {
            'q': query,
            'tbm': 'shop',  # Shopping mode
            'udm': '28'      # Shopping unified mode
        }
        
        # Use a real browser user agent
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        })
        
        response = self.session.get(url, params=params, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        return response.text
    
    def extract_callback_url(self, html: str) -> Optional[str]:
        """
        Extract the callback URL from the HTML response
        The callback URL contains the actual product data
        """
        # Look for callback URLs in various formats
        patterns = [
            r'(/async/callback:\d+\?[^"\'\s<>]+)',  # Full callback URL
            r'"(/async/callback[^"]+)"',             # Quoted callback
            r'href="(/async/callback[^"]+)"',       # href attribute
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if 'fc=' in match:
                    return 'https://www.google.com' + match
        
        return None
    
    def call_callback_endpoint(self, callback_url: str) -> str:
        """Call the callback endpoint directly"""
        response = self.session.get(callback_url, timeout=15)
        response.raise_for_status()
        
        # Remove XSSI protection
        content = response.text
        if content.startswith(')]}\''):
            content = content[4:]
        
        return content
    
    def parse_products(self, html: str) -> List[Dict]:
        """Parse products from HTML response"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all product containers
        product_containers = soup.find_all('div', class_='liKJmf')
        
        products = []
        for container in product_containers:
            try:
                product = GoogleShoppingProduct(container)
                product_dict = product.to_dict()
                
                # Only include products with at least a title and price
                if product_dict.get('title') and product_dict.get('price'):
                    products.append(product_dict)
            except Exception as e:
                print(f"Error parsing product: {e}")
                continue
        
        return products
    
    def search(self, query: str) -> List[Dict]:
        """
        Search Google Shopping for products - REQUESTS ONLY!
        
        Args:
            query: Search query (e.g., "milk", "eggs", "bread")
        
        Returns:
            List of product dictionaries with price, merchant, rating, etc.
        """
        print(f"🔍 Searching for: {query}")
        
        # Step 1: Load initial page (this will have embedded callback URL)
        print("   → Loading Google Shopping...")
        initial_html = self.get_initial_page(query)
        
        # Step 2: Try to extract callback URL
        print("   → Looking for callback endpoint...")
        callback_url = self.extract_callback_url(initial_html)
        
        if callback_url:
            print(f"   ✅ Found callback URL")
            
            # Step 3: Call callback endpoint to get product data
            print("   → Fetching product data...")
            try:
                callback_html = self.call_callback_endpoint(callback_url)
                
                # Step 4: Parse products
                print("   → Parsing products...")
                products = self.parse_products(callback_html)
                
                print(f"   ✅ Found {len(products)} products")
                return products
                
            except Exception as e:
                print(f"   ⚠️  Callback failed: {e}")
        
        # Fallback: Try to parse the initial page directly
        print("   → Trying to parse initial HTML...")
        products = self.parse_products(initial_html)
        
        if not products:
            print("   ❌ No products found - Google may be blocking")
            print("   💡 Try running from a different IP or with a delay")
        
        print(f"   ✅ Found {len(products)} products")
        return products
    
    def search_with_callback_url(self, callback_url: str) -> List[Dict]:
        """
        FAST MODE: Use a pre-captured callback URL (REQUESTS ONLY!)
        
        This is the RECOMMENDED method because:
        - 100% requests-only
        - No browser needed
        - Super fast (one HTTP call)
        - No bot detection issues
        
        Args:
            callback_url: The full callback URL from Chrome DevTools
        
        Returns:
            List of product dictionaries
        """
        print(f"🚀 FAST MODE: Using provided callback URL")
        
        # Fetch data
        print("   → Fetching product data...")
        html = self.call_callback_endpoint(callback_url)
        
        # Parse products
        print("   → Parsing products...")
        products = self.parse_products(html)
        
        print(f"   ✅ Found {len(products)} products")
        
        return products


def main():
    """Demo the scraper - PURE REQUESTS!"""
    scraper = GoogleShoppingScraper()
    
    print("="*80)
    print("GOOGLE SHOPPING SCRAPER - REQUESTS ONLY")
    print("="*80)
    
    # Use the callback URL from the user's earlier capture
    # This proves the concept works!
    callback_url = "https://www.google.com/async/callback:6948?fc=EvcCCrcCQUxrdF92R2wzYmNoR3dyM3FNS0pJUU1pdUU1M0x4b195X2pzTUMwcy1Qekc4N0RGbXEyYnozQk9RdEZBMml2WWpNM2VBakVRM2FVSXU0eVc1TGpRazBlNVA2S1JYRXREYmlzVTRzcWRvR3hDYkVqam9mMTZ6eDFIVWFzZktGNVJueWgtelFmdjl2OS1BZXd6QkdYV3kzNEJzUzIzeVhpUnBjZGJ3d0hvYmtyMmlvNS1qUU1VZXZVMTROSWZoYTU0NjBnY3pnNnBtVENTR3NHc1N1OThqWEo1elpTRmNsa1kzYjR3ZXhLUEt3MzNmN01NR3BIR0laMGlMQTlBTlBRMTZMN000eERnelJzQkdWYnZRa2k4LXhub1R6RERwSUk1MEVvYmx4LUh2OXRQTnMzbWxkaFFFbUUSF1JHa1dhZURWTXRiVjVOb1A0NVNhOEFFGiJBRk1BR0dxNXQybmRwVldHQ3BWenl0blBqbDJYejdYUGRB&fcv=3&vet=12ahUKEwjgh5q-o_CQAxXWKlkFHWOKBh4Q9pcOegQIBhAB..i&ei=RGkWaeDVMtbV5NoP45Sa8AE&opi=95576897&sca_esv=4af503ebc609abd2&shopmd=1&udm=28&yv=3&cs=0&async=_fmt:prog,_id:fc_RGkWaeDVMtbV5NoP45Sa8AE_1"
    
    products = scraper.search_with_callback_url(callback_url)
    
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
    print(f"✅ Total: {len(products)} products")
    print("="*80)
    
    # Save full results
    with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/products.json', 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f"\n💾 Saved to products.json")
    print("\n" + "="*80)
    print("✅ 100% REQUESTS-ONLY - NO BROWSER!")
    print("="*80)


if __name__ == "__main__":
    main()

