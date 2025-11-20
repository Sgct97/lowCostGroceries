#!/usr/bin/env python3
"""
Test CROSS-STORE searching
The whole point: Find cheapest product across ALL stores in user's area!
"""

from playwright.sync_api import sync_playwright
import json
import time

def search_all_stores(query="milk", zipcode="10001"):
    """
    Search across ALL stores in the area
    This is what the user's app should do!
    """
    
    print("="*80)
    print(f"CROSS-STORE SEARCH: '{query}' in {zipcode}")
    print("="*80)
    
    captured_products = []
    
    def handle_response(response):
        nonlocal captured_products
        
        url = response.url
        
        if 'graphql' in url and response.status == 200:
            try:
                if 'SearchResults' in url or 'Search' in url:
                    data = response.json()
                    products = extract_products(data)
                    if products:
                        captured_products.extend(products)
                        print(f"  📦 Captured {len(products)} products from API call")
            except:
                pass
    
    # Load cookies
    try:
        with open('cookies_with_popup_handled.json', 'r') as f:
            cookies = json.load(f)
    except:
        cookies = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        if cookies:
            # Add cookies properly
            for cookie in cookies:
                if 'domain' not in cookie:
                    cookie['domain'] = '.instacart.com'
            context.add_cookies(cookies)
        
        page = context.new_page()
        page.on('response', handle_response)
        
        # Navigate to CROSS-RETAILER search (not specific store!)
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        
        # This is the key: search WITHOUT specifying a store
        search_url = f'https://www.instacart.com/store/search?q={encoded_query}'
        
        print(f"\n[1] Searching across ALL stores...")
        print(f"    URL: {search_url}")
        
        try:
            page.goto(search_url, wait_until='domcontentloaded', timeout=20000)
            time.sleep(8)  # Wait for results
            
            # Scroll to load more
            page.evaluate('window.scrollBy(0, 1000)')
            time.sleep(3)
            
        except Exception as e:
            print(f"    Error: {e}")
        
        browser.close()
    
    # Deduplicate
    unique_products = deduplicate(captured_products)
    
    return unique_products


def extract_products(data, depth=0):
    """Extract products with STORE information"""
    if depth > 25:
        return []
    
    products = []
    
    if isinstance(data, dict):
        if 'name' in data and isinstance(data.get('name'), str) and len(data.get('name', '')) > 3:
            if any(k in data for k in ['brand', 'brandName', 'price', 'size']):
                # Extract price
                price_str = None
                if 'price' in data and isinstance(data['price'], dict):
                    try:
                        price_obj = data['price']
                        price_str = (
                            price_obj.get('viewSection', {}).get('itemCard', {}).get('priceAriaLabelString') or
                            price_obj.get('viewSection', {}).get('priceString')
                        )
                    except:
                        pass
                
                # Try to extract store/retailer information
                store_name = None
                if 'retailer' in data:
                    store_name = data['retailer'].get('name')
                elif 'trackingProperties' in data:
                    # Look in tracking properties
                    tracking = data.get('trackingProperties', {})
                    if isinstance(tracking, dict):
                        store_name = tracking.get('retailer_name') or tracking.get('store_name')
                
                products.append({
                    'name': data.get('name'),
                    'brand': data.get('brand') or data.get('brandName'),
                    'size': data.get('size'),
                    'price': price_str,
                    'store': store_name  # THIS IS KEY!
                })
                return products
        
        for val in data.values():
            if isinstance(val, (dict, list)):
                products.extend(extract_products(val, depth + 1))
    elif isinstance(data, list):
        for item in data:
            products.extend(extract_products(item, depth + 1))
    
    return products


def deduplicate(products):
    """Deduplicate but keep store info"""
    seen = set()
    unique = []
    for p in products:
        key = f"{p['name']}_{p['size']}_{p.get('store')}"
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def analyze_cross_store_results(products, query):
    """Analyze products from multiple stores"""
    
    print(f"\n{'='*80}")
    print(f"CROSS-STORE RESULTS FOR: '{query}'")
    print("="*80)
    
    with_prices = [p for p in products if p.get('price')]
    
    print(f"\nTotal products: {len(products)}")
    print(f"With prices: {len(with_prices)}")
    
    if not with_prices:
        print("\n⚠️  No products with prices found")
        return
    
    # Group by store
    stores = {}
    for p in with_prices:
        store = p.get('store') or 'Unknown Store'
        if store not in stores:
            stores[store] = []
        stores[store].append(p)
    
    print(f"\nStores found: {len(stores)}")
    for store, products_list in stores.items():
        print(f"  - {store}: {len(products_list)} products")
    
    # Find cheapest across ALL stores
    print(f"\n{'='*80}")
    print("CHEAPEST OPTIONS (ACROSS ALL STORES):")
    print("="*80)
    
    def get_price_num(p):
        try:
            price_str = p['price'].replace('$','').replace(',','')
            # Handle "per package" or other text
            if ' ' in price_str:
                price_str = price_str.split()[0]
            return float(price_str)
        except:
            return 999999
    
    sorted_all = sorted(with_prices, key=get_price_num)
    
    for i, p in enumerate(sorted_all[:10], 1):
        print(f"\n{i}. {p['name'][:55]}")
        print(f"   Store: {p.get('store') or 'Unknown'}")
        print(f"   Price: {p['price']}")
        print(f"   Size: {p['size']}")
    
    # Compare price ranges by store
    if len(stores) > 1:
        print(f"\n{'='*80}")
        print("PRICE COMPARISON BY STORE:")
        print("="*80)
        
        for store, products_list in stores.items():
            prices = [get_price_num(p) for p in products_list]
            valid_prices = [p for p in prices if p < 999999]
            
            if valid_prices:
                print(f"\n{store}:")
                print(f"  Price range: ${min(valid_prices):.2f} - ${max(valid_prices):.2f}")
                print(f"  Average: ${sum(valid_prices)/len(valid_prices):.2f}")


if __name__ == "__main__":
    print("="*80)
    print("TESTING CROSS-STORE SEARCH")
    print("This is the REAL value of your app!")
    print("="*80)
    
    # Test cross-store search
    products = search_all_stores("milk", "10001")
    
    if products:
        analyze_cross_store_results(products, "milk")
        
        print(f"\n{'='*80}")
        print("VERDICT")
        print("="*80)
        
        stores_found = len(set(p.get('store') for p in products if p.get('store')))
        
        if stores_found > 1:
            print(f"\n🎉 SUCCESS! Found products from {stores_found} different stores!")
            print("\n✅ Cross-store search WORKS!")
            print("✅ This is EXACTLY what your app needs!")
            print("\nUser gets:")
            print("  - Products from multiple stores")
            print("  - True cheapest option (not just one store)")
            print("  - Real comparison shopping")
        else:
            print(f"\n⚠️  Only found products from {stores_found} store")
            print("\nThis might mean:")
            print("  - Need to adjust search approach")
            print("  - OR search each major store separately")
            print("  - Then combine and compare results")
    else:
        print("\n✗ No products captured")
        print("Need to debug cross-store search approach")

