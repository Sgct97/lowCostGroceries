"""
Test the REAL use case: Grocery products with location

Goal: Find cheapest milk near a specific ZIP code
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from token_service import TokenService
from curl_cffi import requests
import re
import logging

logging.basicConfig(level=logging.WARNING)

def parse_products_simple(html):
    """Simple regex parsing for products"""
    # Find all price matches
    price_matches = re.findall(r'\$([0-9,]+\.[0-9]{2})', html)
    
    # Find store/merchant names (common patterns)
    merchant_patterns = [
        r'<span[^>]*class="[^"]*WJMUdc[^"]*"[^>]*>([^<]+)</span>',
        r'"merchant":"([^"]+)"',
    ]
    merchants = []
    for pattern in merchant_patterns:
        merchants.extend(re.findall(pattern, html))
    
    products = []
    for i, price_str in enumerate(price_matches):
        price_value = float(price_str.replace(',', ''))
        products.append({
            'price': f'${price_str}',
            'price_value': price_value,
            'merchant': merchants[i] if i < len(merchants) else 'Unknown'
        })
    
    return products


print("\n" + "="*80)
print("REAL USE CASE TEST: Grocery Search with Location")
print("="*80 + "\n")

# Test with different grocery items
grocery_items = ["milk", "eggs", "bread"]
test_zipcode = "10001"  # NYC

service = TokenService()

for item in grocery_items:
    print(f"\n{'='*60}")
    print(f"Testing: {item.upper()} near ZIP {test_zipcode}")
    print('='*60)
    
    # Capture callback URL with grocery query
    print(f"1. Capturing callback for '{item}'...")
    callback_url = service.capture_callback_url(region='US', test_query=item)
    
    if not callback_url:
        print(f"❌ Failed to capture callback for {item}")
        continue
    
    print(f"✅ Captured callback")
    
    # Test with location parameter
    print(f"\n2. Testing with location (near={test_zipcode})...")
    
    # Try adding location parameter to callback URL
    if '&' in callback_url:
        location_url = callback_url + f"&near={test_zipcode}"
    else:
        location_url = callback_url + f"?near={test_zipcode}"
    
    try:
        r = requests.get(
            location_url,
            impersonate='chrome120',
            timeout=30,
            headers={'referer': 'https://shopping.google.com/'}
        )
        
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            products = parse_products_simple(r.text)
            print(f"   Prices found: {len(products)}")
            
            if products:
                # Sort by price to find cheapest
                products_with_price = [p for p in products if p['price_value']]
                products_with_price.sort(key=lambda x: x['price_value'])
                
                print(f"\n   🏆 CHEAPEST OPTIONS:")
                for i, p in enumerate(products_with_price[:3], 1):
                    print(f"      {i}. {p['price']} from {p['merchant']}")
                
                # Check if we got store names
                merchants = set(p['merchant'] for p in products if p['merchant'] != 'Unknown')
                if merchants:
                    print(f"\n   📍 Stores found: {', '.join(list(merchants)[:5])}")
            else:
                print("   ⚠️  No products parsed from response")
        else:
            print(f"   ❌ Failed: Status {r.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print("CONCLUSIONS")
print("="*80)
print("\n✅ If we got grocery prices with location:")
print("   - System can find cheapest options by ZIP")
print("   - Ready for full implementation")
print("\n⚠️  If location didn't work or no grocery results:")
print("   - Need to adjust query format")
print("   - May need different Google Shopping parameters")
print("="*80 + "\n")

