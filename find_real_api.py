import requests
import json
import re

def test_google_shopping_apis():
    """Find the real API endpoints Google Shopping uses"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
    }
    
    print("Testing Google Shopping Internal API Endpoints")
    print("="*80)
    
    # Method 1: Try the /async/ium endpoint (used by Google Shopping)
    print("\n1. Testing /async/ium endpoint...")
    url = "https://www.google.com/async/ium?yv=3"
    
    # This is the pattern Google uses for product searches
    params = {
        'q': 'milk',
        'tbm': 'shop',
        'hl': 'en',
        'gl': 'us',
        'async': '_id:iu_async,_fmt:pc'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response length: {len(response.text):,} chars")
        
        if response.status_code == 200:
            # Save response
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/api_response_1.txt', 'w') as f:
                f.write(response.text[:10000])
            print("✓ Saved to api_response_1.txt")
            
            # Check if it has product data
            if any(x in response.text.lower() for x in ['price', 'product', 'merchant']):
                print("✓ Contains product-related data!")
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 2: Try shopping-specific search endpoint
    print("\n2. Testing shopping search endpoint...")
    url = "https://www.google.com/search"
    params = {
        'q': 'milk',
        'tbm': 'shop',
        'hl': 'en',
        'gl': 'us',
        'near': '10001',
        'output': 'search',
        'uule': 'w+CAIQICINdW5pdGVkIHN0YXRlcw',  # Location encoding
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        # Look for embedded JSON in a different way
        if 'data-async-context' in response.text:
            print("✓ Found data-async-context (has AJAX data)")
        
        # Extract any base64 or encoded data
        encoded = re.findall(r'data-async-context="([^"]+)"', response.text)
        if encoded:
            print(f"✓ Found {len(encoded)} async context tokens")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 3: Check for the actual Shopping API pattern
    print("\n3. Testing direct shopping API pattern...")
    
    # Google sometimes uses this pattern for shopping
    test_urls = [
        "https://www.google.com/shopping/product/",
        "https://www.google.com/m/shopping",  # Mobile version
        "https://shopping.google.com/m/search",
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"{url}: {response.status_code}")
        except Exception as e:
            print(f"{url}: Error - {str(e)[:50]}")
    
    # Method 4: Try to replicate what the browser does
    print("\n4. Testing with more realistic browser parameters...")
    
    url = "https://www.google.com/search"
    
    # These params are closer to what a real browser sends
    params = {
        'q': 'organic milk gallon',
        'tbm': 'shop',
        'hl': 'en',
        'gl': 'us',
        'psb': '1',  # Enable product search
        'ved': '0ahUKEwj',
        'ei': 'test'
    }
    
    headers_full = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers_full, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response size: {len(response.text):,} chars")
        
        # Look for specific data markers
        markers = {
            'Product data': '"og:product"',
            'Price data': '"price"',
            'Merchant data': '"merchant"',
            'Availability': '"availability"',
            'Image data': '"image"',
        }
        
        found = []
        for name, marker in markers.items():
            if marker in response.text:
                count = response.text.count(marker)
                found.append(f"{name}: {count}")
        
        if found:
            print("✓ Found data markers:")
            for item in found:
                print(f"  - {item}")
        
        # Save this response
        with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/api_response_2.html', 'w') as f:
            f.write(response.text)
        print("✓ Saved full response to api_response_2.html")
        
    except Exception as e:
        print(f"Error: {e}")

def test_mobile_endpoint():
    """Google's mobile endpoints often return cleaner data"""
    
    print("\n" + "="*80)
    print("5. Testing MOBILE endpoints (often simpler)...")
    print("="*80)
    
    url = "https://www.google.com/search"
    params = {
        'q': 'milk',
        'tbm': 'shop',
        'hl': 'en',
    }
    
    # Mobile user agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response size: {len(response.text):,} chars")
        
        # Mobile version might have simpler HTML with data attributes
        soup_check = {
            'data-docid': response.text.count('data-docid'),
            'data-price': response.text.count('data-price'),
            'data-merchant': response.text.count('data-merchant'),
            'sh-dlr__list-result': response.text.count('sh-dlr__list-result'),
            'price patterns ($X.XX)': len(re.findall(r'\$\d+\.\d{2}', response.text)),
        }
        
        print("\nData attributes found:")
        for attr, count in soup_check.items():
            if count > 0:
                print(f"  ✓ {attr}: {count}")
        
        # Save mobile response
        with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/mobile_response.html', 'w') as f:
            f.write(response.text)
        print("✓ Saved to mobile_response.html")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_google_shopping_apis()
    test_mobile_endpoint()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("1. Check the saved response files for actual data structure")
    print("2. If data found, we can parse it")
    print("3. If still JavaScript-heavy, we'll use lighter headless approach")
    print("="*80)

