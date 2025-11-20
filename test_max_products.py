#!/usr/bin/env python3
"""
Test: How many products can we capture with scrolling?
Goal: Maximize product capture for better filtering options
"""

from playwright.sync_api import sync_playwright
import json
import time

def capture_with_progressive_scrolling(query="milk", store="costco", scroll_attempts=5):
    """
    Capture products with progressive scrolling
    See how many products we can get
    """
    
    print("="*80)
    print(f"MAXIMIZING PRODUCT CAPTURE: '{query}'")
    print("="*80)
    
    captured_products = []
    product_ids = set()  # Track unique products
    
    def handle_response(response):
        nonlocal captured_products, product_ids
        
        url = response.url
        
        if 'graphql' in url and response.status == 200:
            try:
                if 'SearchResults' in url or 'Items' in url:
                    data = response.json()
                    products = extract_products(data)
                    
                    # Add only unique products
                    for p in products:
                        # Use name + size as unique identifier
                        product_id = f"{p.get('name')}_{p.get('size')}"
                        if product_id not in product_ids:
                            product_ids.add(product_id)
                            captured_products.append(p)
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
            context.add_cookies(cookies)
        
        page = context.new_page()
        page.on('response', handle_response)
        
        # Navigate to search
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f'https://www.instacart.com/store/{store}/search_v3/{encoded_query}'
        
        print(f"\n[1] Loading search page...")
        try:
            page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
            time.sleep(5)
            
            print(f"    Initial capture: {len(captured_products)} products")
            
            # Progressive scrolling
            print(f"\n[2] Scrolling to load more products...")
            for i in range(scroll_attempts):
                initial_count = len(captured_products)
                
                # Scroll down
                page.evaluate(f'window.scrollBy(0, {1000 * (i+1)})')
                time.sleep(3)  # Wait for new products to load
                
                new_count = len(captured_products)
                added = new_count - initial_count
                
                print(f"    Scroll {i+1}: +{added} products (total: {new_count})")
                
                # If no new products in last 2 scrolls, we've hit the end
                if i > 1 and added == 0:
                    print(f"    → No new products, stopping")
                    break
            
            print(f"\n[3] Final capture: {len(captured_products)} products")
            
        except Exception as e:
            print(f"    Error: {e}")
        
        browser.close()
    
    return captured_products


def extract_products(data, depth=0):
    """Extract products from API response"""
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
                
                products.append({
                    'name': data.get('name'),
                    'brand': data.get('brand') or data.get('brandName'),
                    'size': data.get('size'),
                    'price': price_str
                })
                return products
        
        for val in data.values():
            if isinstance(val, (dict, list)):
                products.extend(extract_products(val, depth + 1))
    elif isinstance(data, list):
        for item in data:
            products.extend(extract_products(item, depth + 1))
    
    return products


def analyze_product_variety(products, query):
    """Analyze the variety of products captured"""
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS: '{query}' Products")
    print("="*80)
    
    with_prices = [p for p in products if p.get('price')]
    
    print(f"\nTotal products: {len(products)}")
    print(f"With prices: {len(with_prices)}")
    
    if not with_prices:
        return
    
    # Analyze variety
    types = set()
    sizes = set()
    brands = set()
    
    for p in with_prices:
        name = (p.get('name') or '').lower()
        size = (p.get('size') or '').lower()
        brand = (p.get('brand') or '').lower()
        
        # Extract types
        if 'whole' in name:
            types.add('whole')
        if '2%' in name or 'reduced fat' in name:
            types.add('2%')
        if 'skim' in name or 'fat free' in name:
            types.add('skim')
        if 'organic' in name:
            types.add('organic')
        if 'chocolate' in name:
            types.add('chocolate')
        if 'almond' in name or 'oat' in name or 'soy' in name:
            types.add('non-dairy')
        
        # Extract sizes
        if size:
            sizes.add(size)
        
        # Extract brands
        if brand:
            brands.add(brand)
    
    print(f"\nVariety captured:")
    print(f"  Types: {len(types)} ({', '.join(sorted(types))})")
    print(f"  Sizes: {len(sizes)}")
    print(f"  Brands: {len(brands)}")
    
    # Price range
    prices = []
    for p in with_prices:
        try:
            price_num = float(p['price'].replace('$', '').replace(',', ''))
            prices.append(price_num)
        except:
            pass
    
    if prices:
        print(f"\nPrice range: ${min(prices):.2f} - ${max(prices):.2f}")
    
    # Show sample of variety
    print(f"\nSample products (showing variety):")
    shown_types = set()
    count = 0
    for p in with_prices:
        name = (p.get('name') or '').lower()
        
        # Try to show different types
        product_type = None
        if 'whole' in name and 'whole' not in shown_types:
            product_type = 'whole'
        elif '2%' in name and '2%' not in shown_types:
            product_type = '2%'
        elif 'skim' in name and 'skim' not in shown_types:
            product_type = 'skim'
        elif 'organic' in name and 'organic' not in shown_types:
            product_type = 'organic'
        elif 'almond' in name and 'non-dairy' not in shown_types:
            product_type = 'non-dairy'
        
        if product_type:
            shown_types.add(product_type)
            print(f"\n  {p['name'][:60]}")
            print(f"    Price: {p['price']}, Size: {p['size']}")
            count += 1
            
            if count >= 5:
                break


def test_multiple_items():
    """Test maximum capture for multiple common items"""
    
    print("="*80)
    print("TESTING MAXIMUM PRODUCT CAPTURE")
    print("="*80)
    
    test_items = ["milk", "eggs", "bread"]
    
    results = {}
    
    for item in test_items:
        print(f"\n\n{'='*80}")
        print(f"ITEM: {item.upper()}")
        print("="*80)
        
        products = capture_with_progressive_scrolling(item, scroll_attempts=5)
        results[item] = products
        
        if products:
            analyze_product_variety(products, item)
        
        # Brief pause between searches
        time.sleep(2)
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for item, products in results.items():
        with_prices = [p for p in products if p.get('price')]
        print(f"\n{item.title()}:")
        print(f"  Total products: {len(products)}")
        print(f"  With prices: {len(with_prices)}")
        
        if with_prices:
            prices = []
            for p in with_prices:
                try:
                    prices.append(float(p['price'].replace('$','').replace(',','')))
                except:
                    pass
            
            if prices:
                print(f"  Price range: ${min(prices):.2f} - ${max(prices):.2f}")
                print(f"  → User has {len(with_prices)} options to choose from!")
    
    avg_products = sum(len(p) for p in results.values()) / len(results)
    
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print("="*80)
    
    print(f"\nAverage products per search: {avg_products:.0f}")
    
    if avg_products >= 30:
        print("\n✅ EXCELLENT! We're capturing 30+ products per search")
        print("✅ With scrolling, we get comprehensive product coverage")
        print("✅ Plenty of variety for user filtering")
    elif avg_products >= 20:
        print("\n✅ GOOD! We're capturing 20+ products per search")
        print("✅ Sufficient variety for finding cheapest options")
    else:
        print("\n⚠️  Getting fewer products than expected")
        print("   May need to adjust scrolling strategy")
    
    print("\n💡 For your app:")
    print(f"  - Broad search (e.g., 'milk') captures {avg_products:.0f}+ products")
    print("  - Covers multiple types, sizes, brands")
    print("  - User can filter to exact preference")
    print("  - Find cheapest match every time")


if __name__ == "__main__":
    test_multiple_items()

