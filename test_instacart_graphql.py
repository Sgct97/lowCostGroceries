#!/usr/bin/env python3
"""
Test Instacart GraphQL endpoints with captured queries
FINAL FEASIBILITY TEST
"""

import requests
import json
import urllib.parse

def test_graphql_endpoints():
    print("="*80)
    print("TESTING INSTACART GRAPHQL PRODUCT ENDPOINTS")
    print("="*80)
    
    session = requests.Session()
    
    # Load captured API calls
    with open('instacart_api_calls.json', 'r') as f:
        all_calls = json.load(f)
    
    # Extract relevant calls
    target_operations = ['Items', 'SearchCrossRetailerGroupResults', 'Autosuggestions']
    
    results = {}
    
    for op_name in target_operations:
        print(f"\n{'='*80}")
        print(f"Testing: {op_name}")
        print("="*80)
        
        # Find a call with this operation
        matching_calls = [c for c in all_calls if f'operationName={op_name}' in c['url']]
        
        if not matching_calls:
            print(f"No calls found for {op_name}")
            continue
        
        # Try first matching call
        call = matching_calls[0]
        url = call['url']
        
        print(f"URL: {url[:100]}...")
        
        # Prepare headers from captured call
        headers = {
            'User-Agent': call['headers'].get('user-agent', ''),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.instacart.com/',
        }
        
        # Add any important headers
        for key in ['x-client-identifier', 'x-instacart-client', 'authorization']:
            if key in call['headers']:
                headers[key] = call['headers'][key]
        
        try:
            response = session.get(url, headers=headers, timeout=10)
            print(f"\nStatus: {response.status_code}")
            print(f"Size: {len(response.text)} bytes")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Save response
                    filename = f'instacart_{op_name}_response.json'
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"Saved to: {filename}")
                    
                    # Analyze the response
                    data_str = json.dumps(data)
                    
                    # Check for product data
                    has_products = 'product' in data_str.lower()
                    has_prices = 'price' in data_str.lower()
                    has_names = 'name' in data_str.lower()
                    
                    print(f"\nData analysis:")
                    print(f"  Contains 'product': {has_products}")
                    print(f"  Contains 'price': {has_prices}")
                    print(f"  Contains 'name': {has_names}")
                    
                    # Try to extract actual products
                    if has_products:
                        products = extract_products_from_response(data)
                        if products:
                            print(f"  ✓✓✓ EXTRACTED {len(products)} PRODUCTS!")
                            
                            # Show first product
                            if len(products) > 0:
                                print(f"\nFirst product:")
                                print(json.dumps(products[0], indent=2)[:500])
                            
                            results[op_name] = {
                                'success': True,
                                'product_count': len(products),
                                'sample': products[0] if products else None
                            }
                        else:
                            results[op_name] = {'success': False, 'reason': 'No products extracted'}
                    else:
                        results[op_name] = {'success': False, 'reason': 'No product data in response'}
                        
                except json.JSONDecodeError as e:
                    print(f"  Not JSON: {e}")
                    print(f"  First 200 chars: {response.text[:200]}")
                    results[op_name] = {'success': False, 'reason': 'Not JSON'}
            else:
                print(f"  Error response: {response.text[:200]}")
                results[op_name] = {'success': False, 'reason': f'Status {response.status_code}'}
                
        except Exception as e:
            print(f"  Exception: {e}")
            results[op_name] = {'success': False, 'reason': str(e)}
    
    return results


def extract_products_from_response(data, max_depth=10, current_depth=0):
    """Recursively extract product information"""
    products = []
    
    if current_depth > max_depth:
        return products
    
    if isinstance(data, dict):
        # Check if this dict is a product
        if 'name' in data and ('price' in data or 'viewPrice' in data or 'amount' in data):
            products.append(data)
            return products
        
        # Check for common product array keys
        for key in ['items', 'products', 'edges', 'nodes', 'results']:
            if key in data:
                val = data[key]
                if isinstance(val, list):
                    for item in val:
                        products.extend(extract_products_from_response(item, max_depth, current_depth + 1))
        
        # Recursively search other keys
        if not products:
            for val in data.values():
                if isinstance(val, (dict, list)):
                    found = extract_products_from_response(val, max_depth, current_depth + 1)
                    products.extend(found)
                    if products:  # Stop after finding some
                        break
                        
    elif isinstance(data, list):
        for item in data:
            products.extend(extract_products_from_response(item, max_depth, current_depth + 1))
    
    return products


def main():
    results = test_graphql_endpoints()
    
    print("\n" + "="*80)
    print("FINAL FEASIBILITY VERDICT")
    print("="*80)
    
    successful = {k: v for k, v in results.items() if v.get('success')}
    
    if successful:
        print(f"\n🎉 SUCCESS! {len(successful)}/{len(results)} endpoints returned product data!\n")
        
        for op_name, result in successful.items():
            print(f"✓ {op_name}: {result.get('product_count', 0)} products")
        
        print("\n" + "="*80)
        print("INSTACART SCRAPING ASSESSMENT: HIGHLY FEASIBLE")
        print("="*80)
        print("\n✓ Can access Instacart's GraphQL API")
        print("✓ Can retrieve product data with names and prices")
        print("✓ No browser automation required")
        print("✓ Uses standard HTTP requests")
        print("\nSCALABILITY FOR 25K USERS:")
        print("  - Each user search = ~3-5 API calls")
        print("  - 10 items × 25k users = 250k requests total")
        print("  - With caching + rate limiting: VIABLE")
        print("\nRECOMMENDATION: ✅ USE INSTACART")
        print("\nNEXT STEPS:")
        print("1. Implement session management")
        print("2. Add location/zip code support")
        print("3. Build request caching layer")
        print("4. Test rate limits and implement backoff")
        print("5. Build product comparison logic")
        
    else:
        print(f"\n⚠️  {len(results)} endpoints tested, none returned direct product data")
        print("\nThis suggests:")
        print("- May need session cookies from browser")
        print("- May need authentication tokens")
        print("- Rate limiting or bot detection active")
        print("\nFEASIBILITY: MODERATE")
        print("Would require:")
        print("- Cookie/session extraction from browser")
        print("- OR official Instacart Developer Platform API")
    
    # Save final report
    with open('instacart_final_assessment.json', 'w') as f:
        json.dump({
            'results': results,
            'verdict': 'FEASIBLE' if successful else 'CHALLENGING',
            'successful_endpoints': list(successful.keys()),
            'total_tested': len(results)
        }, f, indent=2)
    
    print("\nFull report saved to: instacart_final_assessment.json")


if __name__ == "__main__":
    main()

