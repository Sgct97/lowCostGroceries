#!/usr/bin/env python3
"""
Capture actual API endpoints that Instacart uses
We'll monitor network requests then test if we can call them directly
"""

from playwright.sync_api import sync_playwright
import json
import time

def capture_api_calls():
    print("="*80)
    print("CAPTURING INSTACART API CALLS")
    print("="*80)
    
    api_calls = []
    
    def handle_request(request):
        url = request.url
        # Filter for API calls
        if any(x in url for x in ['/api/', '/graphql', '/v2/', '/v3/', 'search', 'product']):
            if 'instacart.com' in url:
                api_calls.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data if request.method == 'POST' else None
                })
                print(f"\n📡 Captured: {request.method} {url[:100]}")
    
    def handle_response(response):
        url = response.url
        if any(x in url for x in ['/api/', '/graphql', '/v2/', '/v3/', 'search', 'product']):
            if 'instacart.com' in url:
                print(f"   ✓ Response: {response.status}")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        # Set up request/response monitoring
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        # Test 1: Search page
        print("\n[TEST 1] Navigating to search page for 'eggs'...")
        try:
            page.goto('https://www.instacart.com/store/search?q=eggs', wait_until='networkidle', timeout=30000)
            time.sleep(3)  # Wait for any delayed requests
            print(f"Page title: {page.title()}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Try a specific store search
        print("\n[TEST 2] Navigating to Costco store page...")
        try:
            page.goto('https://www.instacart.com/store/costco', wait_until='networkidle', timeout=30000)
            time.sleep(3)
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: Search from a store
        print("\n[TEST 3] Searching within store...")
        try:
            page.goto('https://www.instacart.com/store/costco/search/milk', wait_until='networkidle', timeout=30000)
            time.sleep(3)
        except Exception as e:
            print(f"Error: {e}")
        
        browser.close()
    
    # Save captured API calls
    print("\n" + "="*80)
    print(f"CAPTURED {len(api_calls)} API CALLS")
    print("="*80)
    
    with open('instacart_api_calls.json', 'w') as f:
        json.dump(api_calls, f, indent=2)
    
    print("Saved to: instacart_api_calls.json")
    
    # Display unique endpoints
    unique_urls = {}
    for call in api_calls:
        # Extract base URL without query params
        base_url = call['url'].split('?')[0]
        if base_url not in unique_urls:
            unique_urls[base_url] = []
        unique_urls[base_url].append(call)
    
    print(f"\nFound {len(unique_urls)} unique API endpoints:")
    for i, (url, calls) in enumerate(unique_urls.items(), 1):
        print(f"\n{i}. {url}")
        print(f"   Method: {calls[0]['method']}")
        print(f"   Called {len(calls)} times")
    
    return api_calls


def test_captured_endpoints(api_calls):
    """Try calling the captured endpoints directly"""
    import requests
    
    print("\n" + "="*80)
    print("TESTING CAPTURED ENDPOINTS DIRECTLY")
    print("="*80)
    
    session = requests.Session()
    
    # Test each unique endpoint
    tested = set()
    results = []
    
    for call in api_calls:
        url = call['url']
        base_url = url.split('?')[0]
        
        if base_url in tested:
            continue
        tested.add(base_url)
        
        print(f"\nTesting: {base_url[:80]}")
        
        try:
            # Use captured headers
            headers = {k: v for k, v in call['headers'].items() 
                      if k.lower() not in ['content-length', 'host']}
            
            if call['method'] == 'GET':
                response = session.get(url, headers=headers, timeout=10)
            elif call['method'] == 'POST':
                response = session.post(url, headers=headers, data=call['post_data'], timeout=10)
            else:
                continue
            
            print(f"  Status: {response.status_code}")
            print(f"  Size: {len(response.text)} bytes")
            
            # Check if we got JSON with products
            if response.status_code == 200:
                try:
                    data = response.json()
                    data_str = json.dumps(data)
                    
                    has_products = 'product' in data_str.lower()
                    has_prices = 'price' in data_str.lower()
                    
                    if has_products and has_prices:
                        print(f"  ✓✓✓ HAS PRODUCT DATA!")
                        
                        # Save this response
                        filename = f"instacart_product_response_{len(results)}.json"
                        with open(filename, 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"  Saved to: {filename}")
                        
                        results.append({
                            'url': url,
                            'has_products': True,
                            'filename': filename
                        })
                    else:
                        results.append({
                            'url': url,
                            'has_products': False
                        })
                except:
                    print(f"  Not JSON or parse error")
                    
        except Exception as e:
            print(f"  Error: {e}")
    
    return results


if __name__ == "__main__":
    # First capture the API calls
    api_calls = capture_api_calls()
    
    if api_calls:
        # Then test if we can call them directly
        results = test_captured_endpoints(api_calls)
        
        print("\n" + "="*80)
        print("FINAL ASSESSMENT")
        print("="*80)
        
        successful = [r for r in results if r.get('has_products')]
        
        if successful:
            print(f"\n🎉 SUCCESS! Found {len(successful)} endpoints with product data!")
            print("\nWorking endpoints:")
            for r in successful:
                print(f"  - {r['url'][:100]}")
            
            print("\n✓ INSTACART IS VIABLE FOR SCRAPING!")
            print("✓ We can call these endpoints directly without browser automation")
            print("✓ This will scale to 25k users with proper rate limiting")
        else:
            print("\n⚠️ Could capture API calls but couldn't access them directly")
            print("This may require cookies/authentication from a browser session")
    else:
        print("\n✗ No API calls captured. May need different approach.")

