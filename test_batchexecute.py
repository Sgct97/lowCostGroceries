import requests
import json

def test_batchexecute_endpoint():
    """
    Google often uses /_/batchexecute for their internal APIs
    This is used across Gmail, Photos, Drive, etc.
    """
    
    print("="*80)
    print("TESTING GOOGLE BATCHEXECUTE PATTERN")
    print("="*80)
    
    # BatchExecute is Google's internal RPC system
    # It takes special formatted parameters
    
    base_url = "https://www.google.com/_/shopping/_/batchexecute"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.google.com',
        'Referer': 'https://www.google.com/search?q=milk&tbm=shop',
    }
    
    # Try GET first
    print("\n1. Testing GET request...")
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code != 404:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {str(e)[:50]}")
    
    # Try POST
    print("\n2. Testing POST request...")
    try:
        # BatchExecute typically needs specific POST data format
        # This is a simplified test
        data = {
            'rpcids': 'ShoppingSearch',
            'f.req': json.dumps([["milk"]]),
        }
        response = requests.post(base_url, headers=headers, data=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response length: {len(response.text)} bytes")
            if len(response.text) > 100:
                print(f"Sample: {response.text[:300]}")
    except Exception as e:
        print(f"Error: {str(e)[:50]}")

def test_shopping_specific_endpoints():
    """Test various shopping-specific endpoint patterns"""
    
    print("\n" + "="*80)
    print("TESTING SHOPPING-SPECIFIC ENDPOINTS")
    print("="*80)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*',
        'Referer': 'https://www.google.com/search?q=milk&tbm=shop',
    }
    
    test_urls = [
        # Direct shopping search
        ('https://www.google.com/shopping/search', {'q': 'milk'}),
        
        # Shopping product listing
        ('https://www.google.com/shopping/product/list', {'q': 'milk'}),
        
        # XHR pattern
        ('https://www.google.com/xjs/_/ss/k=shopping', {}),
        
        # Search with specific format
        ('https://www.google.com/search', {'q': 'milk', 'tbm': 'shop', 'output': 'json'}),
        ('https://www.google.com/search', {'q': 'milk', 'tbm': 'shop', 'format': 'json'}),
        
        # Mobile shopping
        ('https://shopping.google.com/search', {'q': 'milk'}),
        
        # Lens/visual search (sometimes shares endpoints)
        ('https://lens.google.com/v3/shopping', {'q': 'milk'}),
    ]
    
    for url, params in test_urls:
        print(f"\n{'='*80}")
        print(f"Testing: {url}")
        print(f"Params: {params}")
        print('='*80)
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"Size: {len(response.text):,} bytes")
            
            if response.status_code == 200:
                # Check for JSON
                if 'json' in response.headers.get('Content-Type', ''):
                    try:
                        data = response.json()
                        print("✅ JSON Response!")
                        print(f"Keys: {list(data.keys())[:10] if isinstance(data, dict) else 'Array'}")
                    except:
                        pass
                
                # Check for product indicators
                sample = response.text[:1000].lower()
                indicators = ['product', 'price', 'merchant', 'offer']
                found = [ind for ind in indicators if ind in sample]
                if found:
                    print(f"✅ Contains: {found}")
                    
                    # Save promising responses
                    if len(found) >= 2:
                        filename = url.replace('https://', '').replace('/', '_').replace(':', '') + '.txt'
                        with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/{filename}', 'w') as f:
                            f.write(response.text[:5000])
                        print(f"💾 Saved to: {filename}")
        
        except Exception as e:
            print(f"Error: {str(e)[:80]}")

def check_page_for_api_hints():
    """
    Load the shopping page and look for API endpoint hints in the HTML/JS
    """
    
    print("\n" + "="*80)
    print("SCANNING PAGE SOURCE FOR API HINTS")
    print("="*80)
    
    url = "https://www.google.com/search"
    params = {'q': 'milk', 'tbm': 'shop'}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        html = response.text
        
        # Look for API endpoint patterns in the source
        patterns = [
            (r'["\']https://www\.google\.com/[^"\']*(?:api|rpc|async|shopping)[^"\']*["\']', 'Full API URLs'),
            (r'/shopping/[^"\'\s]+', 'Shopping paths'),
            (r'/_/shopping/[^"\'\s]+', 'Internal shopping paths'),
            (r'endpoint["\']?\s*[:=]\s*["\']([^"\']+)', 'Endpoint variables'),
            (r'apiUrl["\']?\s*[:=]\s*["\']([^"\']+)', 'API URL variables'),
        ]
        
        found_any = False
        for pattern, description in patterns:
            import re
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                unique = list(set(matches))[:10]
                print(f"\n✅ {description}:")
                for match in unique:
                    print(f"  - {match}")
                found_any = True
        
        if not found_any:
            print("\n⚠️ No obvious API hints found in page source")
            print("This means the endpoint is likely loaded dynamically")
            print("You MUST use Chrome DevTools to capture it while interacting with the page")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                   ADVANCED ENDPOINT DISCOVERY                            ║
    ║                   Testing Google's internal patterns                     ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    test_batchexecute_endpoint()
    test_shopping_specific_endpoints()
    check_page_for_api_hints()
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("If none of these worked, follow ENDPOINT_HUNTING_GUIDE.md")
    print("You MUST manually capture the request from Chrome DevTools")
    print("The endpoint likely requires specific session/state parameters")
    print("="*80)

