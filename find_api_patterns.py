from curl_cffi import requests
import re

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

# Try different API-like endpoints
test_urls = [
    # Shopping API patterns
    "https://www.google.com/shopping/product/search?q=milk",
    "https://www.google.com/async/bgasy?q=milk&tbm=shop",
    "https://www.google.com/async/shopping?q=milk",
    "https://www.google.com/s?q=milk&tbm=shop&udm=28",
    # Complete/suggest endpoints
    "https://www.google.com/complete/search?q=milk&client=products",
]

print("Testing potential API endpoints:\n")

for url in test_urls:
    try:
        print(f"Testing: {url[:80]}...")
        response = requests.get(
            url,
            headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "accept": "application/json, text/plain, */*"
            },
            proxies={"http": PROXY, "https": PROXY},
            impersonate="chrome120",
            timeout=10
        )
        
        content_type = response.headers.get('Content-Type', '')
        
        print(f"  ✓ Status: {response.status_code}")
        print(f"  ✓ Type: {content_type}")
        print(f"  ✓ Size: {len(response.text):,} bytes")
        
        # Check for JSON
        if 'json' in content_type.lower():
            print(f"  ✓✓ JSON RESPONSE!")
            print(f"  Preview: {response.text[:200]}")
        
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}\n")

