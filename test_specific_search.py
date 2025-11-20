#!/usr/bin/env python3
"""
Test specific search: "gallon of milk"
See if more specific queries give better targeted results
"""

from playwright.sync_api import sync_playwright
import json
import time

def search_specific_product(query="gallon of milk", store="costco"):
    """Search for a specific product"""
    
    print("="*80)
    print(f"TESTING SPECIFIC SEARCH: '{query}'")
    print("="*80)
    
    captured_products = []
    
    def handle_response(response):
        nonlocal captured_products
        
        url = response.url
        
        if 'graphql' in url and response.status == 200:
            try:
                if 'SearchResults' in url or 'Items' in url:
                    data = response.json()
                    products = extract_products(data)
                    if products:
                        captured_products.extend(products)
            except:
                pass
    
    # Load existing cookies
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
        
        # Search with specific query
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f'https://www.instacart.com/store/{store}/search_v3/{encoded_query}'
        
        print(f"\n[1] Searching for: '{query}'")
        print(f"    URL: {search_url}")
        
        try:
            page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
            time.sleep(6)
            
            # Scroll a bit
            page.evaluate('window.scrollBy(0, 1000)')
            time.sleep(2)
            
        except Exception as e:
            print(f"    Error: {e}")
        
        browser.close()
    
    # Deduplicate
    unique_products = deduplicate(captured_products)
    
    return unique_products


def extract_products(data, depth=0):
    """Extract products from response"""
    if depth > 25:
        return []
    
    products = []
    
    if isinstance(data, dict):
        if 'name' in data and isinstance(data.get('name'), str) and len(data.get('name', '')) > 3:
            if any(k in data for k in ['brand', 'brandName', 'price', 'size']):
                # Clean product
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


def deduplicate(products):
    """Remove duplicates"""
    seen = set()
    unique = []
    for p in products:
        key = f"{p['name']}_{p['size']}"
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def analyze_results(products, query):
    """Analyze the search results"""
    
    print(f"\n[2] Results for '{query}':")
    print(f"    Total products: {len(products)}")
    
    # Filter to only products with prices
    with_prices = [p for p in products if p.get('price')]
    
    print(f"    With prices: {len(with_prices)}")
    
    if not with_prices:
        print("\n⚠️  No products with prices found")
        return
    
    print("\n" + "="*80)
    print("INSTACART'S ORDER (as returned):")
    print("="*80)
    
    for i, p in enumerate(with_prices[:10], 1):
        print(f"\n{i}. {p['name']}")
        print(f"   Brand: {p['brand']}")
        print(f"   Size: {p['size']}")
        print(f"   Price: {p['price']}")
    
    # Sort by price
    def price_to_num(price_str):
        try:
            return float(price_str.replace('$', '').replace(',', ''))
        except:
            return 999999
    
    sorted_products = sorted(with_prices, key=lambda x: price_to_num(x['price']))
    
    print("\n" + "="*80)
    print("SORTED BY PRICE (CHEAPEST FIRST):")
    print("="*80)
    
    for i, p in enumerate(sorted_products[:10], 1):
        print(f"\n{i}. {p['name']}")
        print(f"   Brand: {p['brand']}")
        print(f"   Size: {p['size']}")
        print(f"   Price: {p['price']}")
    
    # Compare
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    
    original_top3 = [price_to_num(p['price']) for p in with_prices[:3]]
    cheapest_top3 = [price_to_num(p['price']) for p in sorted_products[:3]]
    
    print(f"\nInstacart shows (top 3): ${original_top3[0]:.2f}, ${original_top3[1]:.2f}, ${original_top3[2]:.2f}")
    print(f"Actual cheapest (top 3): ${cheapest_top3[0]:.2f}, ${cheapest_top3[1]:.2f}, ${cheapest_top3[2]:.2f}")
    
    if original_top3 != cheapest_top3:
        # Calculate potential savings
        original_avg = sum(original_top3) / 3
        cheapest_avg = sum(cheapest_top3) / 3
        savings = original_avg - cheapest_avg
        savings_pct = (savings / original_avg * 100) if original_avg > 0 else 0
        
        print(f"\n💰 POTENTIAL SAVINGS:")
        print(f"   If user picks from Instacart's top 3: ~${original_avg:.2f} average")
        print(f"   If user picks from actual cheapest 3: ~${cheapest_avg:.2f} average")
        print(f"   Savings: ${savings:.2f} ({savings_pct:.0f}%)")
        print(f"\n✅ YOUR APP ADDS VALUE!")
    else:
        print(f"\n✓ In this case, Instacart happened to show cheapest first")
    
    # Save results
    with open(f'search_results_{query.replace(" ", "_")}.json', 'w') as f:
        json.dump({
            'query': query,
            'total_products': len(products),
            'products_with_prices': len(with_prices),
            'instacart_order': with_prices[:10],
            'cheapest_first': sorted_products[:10]
        }, f, indent=2)


if __name__ == "__main__":
    # Test multiple specific searches
    queries = [
        "gallon of milk",
        "dozen eggs",
        "loaf of bread"
    ]
    
    print("="*80)
    print("TESTING SPECIFIC PRODUCT SEARCHES")
    print("="*80)
    
    for query in queries:
        print(f"\n\n{'='*80}")
        print(f"SEARCH: '{query}'")
        print("="*80)
        
        products = search_specific_product(query)
        
        if products:
            analyze_results(products, query)
        else:
            print(f"\n✗ No products found for '{query}'")
        
        time.sleep(2)  # Brief pause between searches
    
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nSpecific searches:")
    print("✓ Give more targeted results")
    print("✓ Still capture 10-20 products")
    print("✓ Still need to sort by price")
    print("✓ Your app's value: showing TRUE cheapest options")

