#!/usr/bin/env python3
"""
Extract actual product data from Instacart search page
"""

import json
import re
from bs4 import BeautifulSoup

def extract_product_data():
    print("="*80)
    print("EXTRACTING PRODUCT DATA FROM INSTACART SEARCH PAGE")
    print("="*80)
    
    with open('instacart_search_page.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for __NEXT_DATA__
    print("\n[1] Looking for Next.js data...")
    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        print("✓ Found __NEXT_DATA__!")
        try:
            data = json.loads(next_data.string)
            
            with open('instacart_extracted_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("✓ Saved full data to: instacart_extracted_data.json")
            
            # Navigate the structure to find products
            print("\n[2] Analyzing data structure...")
            print(f"Top-level keys: {list(data.keys())}")
            
            if 'props' in data:
                props = data['props']
                print(f"Props keys: {list(props.keys())}")
                
                if 'pageProps' in props:
                    page_props = props['pageProps']
                    print(f"PageProps keys: {list(page_props.keys())}")
                    
                    # Look for products in various possible locations
                    products = None
                    if 'products' in page_props:
                        products = page_props['products']
                    elif 'items' in page_props:
                        products = page_props['items']
                    elif 'initialState' in page_props:
                        # Check nested initial state
                        initial = page_props['initialState']
                        if isinstance(initial, dict):
                            # Recursively search for products
                            products = search_for_products(initial)
                    
                    if products:
                        print(f"\n✓✓✓ FOUND PRODUCTS! Count: {len(products) if isinstance(products, list) else 'unknown'}")
                        
                        # Extract and display first product
                        if isinstance(products, list) and len(products) > 0:
                            first_product = products[0]
                            print("\nFirst product structure:")
                            print(json.dumps(first_product, indent=2)[:500])
                            
                            # Try to extract key fields
                            extract_product_fields(products)
                            
                            # Save products
                            with open('instacart_products.json', 'w') as f:
                                json.dump(products, f, indent=2)
                            print(f"\n✓ Saved {len(products)} products to: instacart_products.json")
                            
                            return True
            
            # If we didn't find products in standard location, search entire structure
            print("\n[3] Performing deep search for product data...")
            all_products = search_for_products(data)
            if all_products:
                print(f"✓ Found products in data! Count: {len(all_products) if isinstance(all_products, list) else 'unknown'}")
                with open('instacart_products_deep_search.json', 'w') as f:
                    json.dump(all_products, f, indent=2)
                extract_product_fields(all_products if isinstance(all_products, list) else [all_products])
                return True
                
        except Exception as e:
            print(f"✗ Error parsing Next.js data: {e}")
            import traceback
            traceback.print_exc()
    
    # Alternative: Look for inline JSON
    print("\n[4] Looking for inline JSON data...")
    json_pattern = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL)
    print(f"Found {len(json_pattern)} JSON script blocks")
    
    for i, json_str in enumerate(json_pattern[:3]):  # Check first 3
        try:
            data = json.loads(json_str)
            products = search_for_products(data)
            if products:
                print(f"✓ Found products in JSON block {i}!")
                with open(f'instacart_products_json_block_{i}.json', 'w') as f:
                    json.dump(products, f, indent=2)
                return True
        except:
            pass
    
    # Look for JavaScript variable assignments
    print("\n[5] Looking for JavaScript data...")
    js_patterns = [
        r'var\s+products\s*=\s*(\[.+?\]);',
        r'const\s+products\s*=\s*(\[.+?\]);',
        r'window\.products\s*=\s*(\[.+?\]);',
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            print(f"Found JS pattern: {pattern[:30]}")
            try:
                data = json.loads(matches[0])
                with open('instacart_products_js.json', 'w') as f:
                    json.dump(data, f, indent=2)
                extract_product_fields(data if isinstance(data, list) else [data])
                return True
            except:
                pass
    
    print("\n✗ Could not find product data in expected locations")
    print("The page may require JavaScript execution or authentication")
    return False


def search_for_products(obj, depth=0, max_depth=10):
    """Recursively search for product-like data"""
    if depth > max_depth:
        return None
    
    if isinstance(obj, dict):
        # Check if this looks like a product
        if has_product_fields(obj):
            return obj
        
        # Check for arrays of products
        for key in ['products', 'items', 'results', 'data', 'edges', 'nodes']:
            if key in obj:
                val = obj[key]
                if isinstance(val, list) and len(val) > 0:
                    if has_product_fields(val[0]):
                        return val
        
        # Recursively search all values
        for key, val in obj.items():
            result = search_for_products(val, depth + 1, max_depth)
            if result:
                return result
                
    elif isinstance(obj, list) and len(obj) > 0:
        # Check if this is an array of products
        if has_product_fields(obj[0]):
            return obj
        
        # Search first few items
        for item in obj[:5]:
            result = search_for_products(item, depth + 1, max_depth)
            if result:
                return result
    
    return None


def has_product_fields(obj):
    """Check if object has product-like fields"""
    if not isinstance(obj, dict):
        return False
    
    # Products typically have these fields
    product_indicators = ['name', 'price', 'id']
    score = sum(1 for field in product_indicators if field in obj)
    
    # Also check for grocery-specific fields
    grocery_indicators = ['size', 'unit', 'brand', 'image']
    score += sum(0.5 for field in grocery_indicators if field in obj)
    
    return score >= 2


def extract_product_fields(products):
    """Extract and display useful product fields"""
    print("\n" + "="*80)
    print("PRODUCT DATA ANALYSIS")
    print("="*80)
    
    if not products or len(products) == 0:
        print("No products to analyze")
        return
    
    print(f"\nTotal products: {len(products)}")
    
    # Analyze first product's structure
    first = products[0]
    print(f"\nFields in first product: {list(first.keys())}")
    
    # Display first 3 products
    print("\n" + "-"*80)
    print("SAMPLE PRODUCTS:")
    print("-"*80)
    
    for i, product in enumerate(products[:3], 1):
        print(f"\nProduct {i}:")
        
        # Try to extract common fields
        name = product.get('name') or product.get('title') or product.get('displayName')
        price = product.get('price') or product.get('cost') or product.get('amount')
        size = product.get('size') or product.get('unit') or product.get('quantity')
        brand = product.get('brand') or product.get('manufacturer')
        
        if name:
            print(f"  Name: {name}")
        if price:
            print(f"  Price: {price}")
        if size:
            print(f"  Size: {size}")
        if brand:
            print(f"  Brand: {brand}")
        
        # Show all fields for debugging
        print(f"  All fields: {json.dumps(product, indent=4)[:300]}")
    
    # Generate feasibility report
    print("\n" + "="*80)
    print("FEASIBILITY ASSESSMENT")
    print("="*80)
    
    has_names = any('name' in p or 'title' in p for p in products[:5])
    has_prices = any('price' in p or 'cost' in p for p in products[:5])
    
    print(f"✓ Can extract names: {has_names}")
    print(f"✓ Can extract prices: {has_prices}")
    print(f"✓ Product count: {len(products)}")
    
    if has_names and has_prices:
        print("\n🎉 SUCCESS! We can extract product names and prices from Instacart!")
        print("This means scraping is FEASIBLE for your use case.")
    else:
        print("\n⚠️ Partial success. May need additional work to extract all fields.")


if __name__ == "__main__":
    success = extract_product_data()
    
    if success:
        print("\n" + "="*80)
        print("RECOMMENDATION: INSTACART IS VIABLE!")
        print("="*80)
        print("Next steps:")
        print("1. Implement proper request handling")
        print("2. Add location/zipcode support")
        print("3. Build caching layer for scalability")
        print("4. Test rate limits")
    else:
        print("\n" + "="*80)
        print("Need to investigate further...")
        print("="*80)

