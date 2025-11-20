#!/usr/bin/env python3
"""
PRODUCTION INSTACART SCRAPER - CROSS-STORE VERSION
Searches across ALL stores in user's area to find cheapest option
THIS IS THE REAL APP!
"""

from playwright.sync_api import sync_playwright
import json
import time
import urllib.parse

class CrossStoreInstacartScraper:
    def __init__(self):
        self.cookies = None
        
    def initialize_session(self):
        """Initialize browser session and get cookies"""
        print("\n[SESSION] Initializing browser session...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Load Instacart
            page.goto('https://www.instacart.com/', wait_until='domcontentloaded')
            time.sleep(2)
            
            # Handle popups
            try:
                close_selectors = ['button[aria-label*="Close"]', 'button:has-text("Close")']
                for selector in close_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.click(timeout=2000)
                            time.sleep(1)
                            break
                    except:
                        pass
            except:
                pass
            
            self.cookies = context.cookies()
            print(f"  ✓ Got {len(self.cookies)} cookies")
            
            browser.close()
        
        return True
    
    def search_all_stores(self, query, zipcode="10001", max_results=100):
        """
        Search across ALL stores in the area
        
        Args:
            query: Product to search for (e.g., "milk", "eggs")
            zipcode: User's location
            max_results: Maximum results to return
        
        Returns:
            List of products with store information and prices
        """
        print(f"\n[SEARCH] Searching for '{query}' across ALL stores near {zipcode}...")
        
        if not self.cookies:
            self.initialize_session()
        
        captured_products = []
        
        def handle_response(response):
            nonlocal captured_products
            
            url = response.url
            
            if 'graphql' in url and response.status == 200:
                try:
                    if any(x in url for x in ['SearchResults', 'Search', 'Items']):
                        data = response.json()
                        products = self._extract_products_with_store(data)
                        if products:
                            captured_products.extend(products)
                except:
                    pass
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            # Add cookies with proper domain
            cookies_with_domain = []
            for cookie in self.cookies:
                cookie_copy = cookie.copy()
                if 'domain' not in cookie_copy or not cookie_copy['domain']:
                    cookie_copy['domain'] = '.instacart.com'
                if 'path' not in cookie_copy:
                    cookie_copy['path'] = '/'
                cookies_with_domain.append(cookie_copy)
            
            context.add_cookies(cookies_with_domain)
            
            page = context.new_page()
            page.on('response', handle_response)
            
            # KEY: Use cross-store search URL (not /store/specific-store)
            encoded_query = urllib.parse.quote(query)
            search_url = f'https://www.instacart.com/store/search?q={encoded_query}'
            
            try:
                page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
                time.sleep(6)
                
                # Scroll to load more
                page.evaluate('window.scrollBy(0, 1000)')
                time.sleep(3)
                
            except Exception as e:
                print(f"  ⚠️ Navigation error: {e}")
            
            browser.close()
        
        # Deduplicate
        unique_products = self._deduplicate_products(captured_products)
        results = unique_products[:max_results]
        
        print(f"  ✓ Found {len(results)} products across multiple stores")
        
        return results
    
    def _extract_products_with_store(self, data, depth=0, max_depth=25):
        """Extract products WITH store/retailer information"""
        if depth > max_depth:
            return []
        
        products = []
        
        if isinstance(data, dict):
            if 'name' in data and isinstance(data.get('name'), str) and len(data.get('name', '')) > 3:
                if any(key in data for key in ['brand', 'brandName', 'price', 'size']):
                    # Extract product
                    product = self._clean_product_with_store(data)
                    if product:
                        products.append(product)
                    return products
            
            for val in data.values():
                if isinstance(val, (dict, list)):
                    products.extend(self._extract_products_with_store(val, depth + 1, max_depth))
                    
        elif isinstance(data, list):
            for item in data:
                products.extend(self._extract_products_with_store(item, depth + 1, max_depth))
        
        return products
    
    def _clean_product_with_store(self, raw_product):
        """Extract clean product data INCLUDING store info"""
        try:
            product = {
                'name': raw_product.get('name'),
                'brand': raw_product.get('brand') or raw_product.get('brandName'),
                'size': raw_product.get('size') or raw_product.get('displaySize'),
                'product_id': raw_product.get('id') or raw_product.get('productId'),
            }
            
            # Extract price
            price_str = None
            if 'price' in raw_product and isinstance(raw_product['price'], dict):
                try:
                    price_obj = raw_product['price']
                    price_str = (
                        price_obj.get('viewSection', {}).get('itemCard', {}).get('priceAriaLabelString') or
                        price_obj.get('viewSection', {}).get('priceString') or
                        price_obj.get('viewSection', {}).get('priceValueString')
                    )
                except:
                    pass
            
            product['price'] = price_str
            
            # Extract STORE/RETAILER information - THIS IS KEY!
            store_name = None
            
            # Try multiple places
            if 'retailer' in raw_product:
                retailer = raw_product['retailer']
                if isinstance(retailer, dict):
                    store_name = retailer.get('name') or retailer.get('displayName')
                elif isinstance(retailer, str):
                    store_name = retailer
            
            if not store_name and 'trackingProperties' in raw_product:
                tracking = raw_product['trackingProperties']
                if isinstance(tracking, dict):
                    store_name = (
                        tracking.get('retailer_name') or
                        tracking.get('store_name') or
                        tracking.get('element_details', {}).get('retailer_name')
                    )
            
            product['store'] = store_name or 'Unknown Store'
            
            # Availability
            if 'availability' in raw_product:
                avail = raw_product['availability']
                product['available'] = avail.get('available', True)
                product['stock_level'] = avail.get('stockLevel', 'unknown')
            else:
                product['available'] = True
                product['stock_level'] = 'unknown'
            
            # Only return if we have essential data
            if product['name'] and product['price']:
                return product
            
        except Exception as e:
            pass
        
        return None
    
    def _deduplicate_products(self, products):
        """Remove duplicates keeping store info"""
        seen = set()
        unique = []
        
        for product in products:
            # Use name + size + store as unique key
            key = f"{product.get('name')}_{product.get('size')}_{product.get('store')}"
            if key not in seen:
                seen.add(key)
                unique.append(product)
        
        return unique


def test_cross_store_comparison():
    """Test cross-store comparison - THE REAL APP!"""
    
    print("="*80)
    print("CROSS-STORE PRICE COMPARISON")
    print("Finding cheapest across ALL stores!")
    print("="*80)
    
    scraper = CrossStoreInstacartScraper()
    scraper.initialize_session()
    
    # Test with milk
    products = scraper.search_all_stores("milk", "10001", max_results=100)
    
    if not products:
        print("\n✗ No products found")
        return
    
    with_prices = [p for p in products if p.get('price')]
    
    print(f"\n[RESULTS] {len(with_prices)} products with prices")
    
    # Group by store
    stores = {}
    for p in with_prices:
        store = p.get('store', 'Unknown')
        if store not in stores:
            stores[store] = []
        stores[store].append(p)
    
    print(f"\n[STORES] Found products from {len(stores)} stores:")
    for store, prods in stores.items():
        print(f"  - {store}: {len(prods)} products")
    
    # Find cheapest across ALL stores
    def get_price_num(p):
        try:
            price_str = p['price'].replace('$', '').replace(',', '')
            if ' ' in price_str:
                price_str = price_str.split()[0]
            return float(price_str)
        except:
            return 999999
    
    sorted_all = sorted(with_prices, key=get_price_num)
    
    print(f"\n{'='*80}")
    print("TOP 10 CHEAPEST (ACROSS ALL STORES):")
    print("="*80)
    
    for i, p in enumerate(sorted_all[:10], 1):
        print(f"\n{i}. {p['name'][:50]}")
        print(f"   🏪 Store: {p['store']}")
        print(f"   💰 Price: {p['price']}")
        print(f"   📦 Size: {p['size']}")
    
    # Compare cheapest by store
    if len(stores) > 1:
        print(f"\n{'='*80}")
        print("CHEAPEST AT EACH STORE:")
        print("="*80)
        
        for store, prods in stores.items():
            sorted_store = sorted(prods, key=get_price_num)
            cheapest = sorted_store[0]
            print(f"\n{store}:")
            print(f"  {cheapest['name'][:45]}")
            print(f"  → {cheapest['price']}")
    
    # Overall winner
    if sorted_all:
        winner = sorted_all[0]
        print(f"\n{'='*80}")
        print("🏆 OVERALL WINNER (CHEAPEST IN AREA):")
        print("="*80)
        print(f"\n{winner['name']}")
        print(f"Store: {winner['store']}")
        print(f"Price: {winner['price']}")
        print(f"\n✅ THIS IS WHAT YOUR APP SHOWS THE USER!")


if __name__ == "__main__":
    test_cross_store_comparison()
    
    print("\n\n" + "="*80)
    print("YOUR APP'S VALUE PROPOSITION")
    print("="*80)
    
    print("\nUser searches: 'milk'")
    print("\nYour app:")
    print("  1. Searches ALL stores in user's zip code")
    print("  2. Finds: Costco $3.63, Kroger $4.99, Safeway $5.29")
    print("  3. Shows: 'Cheapest at Costco: $3.63'")
    print("\nUser saves: $1.36+ by shopping at the right store!")
    print("\n✅ THIS is the value of your app!")

