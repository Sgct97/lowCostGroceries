import requests
import json
import re

def test_shopping_rpc_endpoints():
    """Test RPC-style endpoints for Google Shopping (like /maps/rpc/vp)"""
    
    print("="*80)
    print("TESTING GOOGLE SHOPPING RPC ENDPOINTS")
    print("(Similar to /maps/rpc/vp pattern you found)")
    print("="*80)
    
    # Search parameters
    query = "milk"
    zip_code = "10001"
    
    # Headers similar to what Maps API expects
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/search?tbm=shop',
        'Origin': 'https://www.google.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'X-Client-Data': 'test',
    }
    
    # Test RPC-style endpoints (modeled after /maps/rpc/vp)
    rpc_endpoints = [
        {
            'name': 'Shopping RPC VP (Virtual Products)',
            'url': 'https://www.google.com/shopping/rpc/vp',
            'params': {'q': query, 'hl': 'en', 'gl': 'us'}
        },
        {
            'name': 'Shopping RPC Search',
            'url': 'https://www.google.com/shopping/rpc/search',
            'params': {'q': query}
        },
        {
            'name': 'Shopping Underscore RPC',
            'url': 'https://www.google.com/_/shopping/_/rpc',
            'params': {'q': query, 'hl': 'en'}
        },
        {
            'name': 'Async Shopping (like Maps async)',
            'url': 'https://www.google.com/async/shopping',
            'params': {'q': query, 'async': 'search_q:' + query}
        },
        {
            'name': 'Search Async (with shopping)',
            'url': 'https://www.google.com/async/search',
            'params': {'q': query, 'tbm': 'shop', 'async': '_fmt:json'}
        },
    ]
    
    for endpoint in rpc_endpoints:
        print(f"\n{'='*80}")
        print(f"Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        print('='*80)
        
        try:
            # Try GET first (like Maps)
            response = requests.get(
                endpoint['url'],
                params=endpoint['params'],
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"Response size: {len(response.text):,} bytes")
            
            # Check if it's protobuf-wrapped JSON (like Maps returns)
            if response.status_code == 200 and len(response.text) > 100:
                
                # Look for nested array patterns (protobuf format)
                if response.text.startswith(')]}\''):
                    print("✅ Found XSSI protection prefix (like Maps API!)")
                    clean_text = response.text[4:]  # Remove )]}' prefix
                else:
                    clean_text = response.text
                
                # Try to parse as JSON
                try:
                    data = json.loads(clean_text)
                    print("🎉 VALID JSON RESPONSE!")
                    print(f"Type: {type(data)}")
                    
                    if isinstance(data, list):
                        print(f"Array length: {len(data)}")
                        print(f"First element type: {type(data[0]) if data else 'empty'}")
                    elif isinstance(data, dict):
                        print(f"Keys: {list(data.keys())[:10]}")
                    
                    # Save it
                    filename = f'shopping_rpc_{endpoint["name"].replace(" ", "_").replace("/", "_")}.json'
                    with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/{filename}', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"💾 Saved to: {filename}")
                    
                    # Look for product data in the structure
                    json_str = json.dumps(data).lower()
                    indicators = ['price', 'product', 'merchant', 'title', 'offer']
                    found = [ind for ind in indicators if ind in json_str]
                    if found:
                        print(f"✅ FOUND PRODUCT DATA: {found}")
                    
                except json.JSONDecodeError as e:
                    print(f"Not JSON (might be protobuf or HTML)")
                    
                    # Check if it looks like product data anyway
                    sample = response.text[:500].lower()
                    if any(x in sample for x in ['price', 'product', 'merchant']):
                        print("⚠️ Contains product terms but not JSON format")
                        
                        # Save for analysis
                        filename = f'response_{endpoint["name"].replace(" ", "_")}.txt'
                        with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/{filename}', 'w') as f:
                            f.write(response.text[:2000])
                        print(f"💾 Saved sample to: {filename}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")

def test_with_real_browser_params():
    """Test with actual parameters captured from browser (you'll need to update these)"""
    
    print(f"\n{'='*80}")
    print("TESTING WITH REALISTIC BROWSER PARAMETERS")
    print('='*80)
    
    # These would be captured from DevTools - using placeholders for now
    url = "https://www.google.com/search"
    
    params = {
        'q': 'milk',
        'tbm': 'shop',
        'hl': 'en',
        'gl': 'us',
        # Add these if you capture them from browser:
        # 'ved': '...',
        # 'ei': '...',
        # 'sxsrf': '...',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        # Look for any RPC endpoints mentioned in the HTML
        rpc_patterns = [
            r'(/shopping/rpc/[^\s"\']+)',
            r'(/async/[^\s"\']+)',
            r'(/_/shopping/[^\s"\']+)',
        ]
        
        found_endpoints = set()
        for pattern in rpc_patterns:
            matches = re.findall(pattern, response.text)
            found_endpoints.update(matches)
        
        if found_endpoints:
            print(f"\n✅ FOUND RPC ENDPOINTS IN HTML:")
            for endpoint in sorted(found_endpoints)[:10]:
                print(f"  - {endpoint}")
            
            # Save them
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/discovered_endpoints.txt', 'w') as f:
                for endpoint in sorted(found_endpoints):
                    f.write(endpoint + '\n')
            print("\n💾 Saved to: discovered_endpoints.txt")
        else:
            print("⚠️ No obvious RPC endpoints found in HTML")
            
    except Exception as e:
        print(f"Error: {e}")

def manual_discovery_guide():
    """Instructions for manual discovery"""
    
    print(f"\n{'='*80}")
    print("MANUAL DISCOVERY INSTRUCTIONS")
    print('='*80)
    
    print("""
    Since you successfully found /maps/rpc/vp, do the same for Shopping:
    
    1. Open Chrome DevTools (F12)
    2. Go to Network tab
    3. Filter: Fetch/XHR
    4. Clear existing requests
    5. Navigate to: https://www.google.com/search?q=milk&tbm=shop
    6. Look for requests with these patterns:
       ✓ /rpc/
       ✓ /async/
       ✓ /_/shopping/
       ✓ Anything returning JSON/protobuf
    
    7. Check the Response tab for product data
    8. When you find it, copy as cURL and paste here
    
    💡 TIP: The endpoint might load AFTER the initial page load,
           so watch the Network tab for a few seconds.
    """)

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║          GOOGLE SHOPPING RPC ENDPOINT DISCOVERY                          ║
    ║          (Based on your successful /maps/rpc/vp discovery)               ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    test_shopping_rpc_endpoints()
    test_with_real_browser_params()
    manual_discovery_guide()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("1. Check any JSON files that were saved")
    print("2. Follow the manual instructions above if no endpoint found")
    print("3. Once found, we'll build the scraper in < 1 hour")
    print("="*80)

