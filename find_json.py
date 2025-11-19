from curl_cffi import requests
import re
import json

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy_url = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"
proxies = {"http": proxy_url, "https": proxy_url}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}

response = requests.get(
    "https://www.google.com/search?q=milk&tbm=shop",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

print("Looking for embedded JSON data...\n")

# Look for AF_initDataCallback (common Google pattern)
callback_pattern = r'AF_initDataCallback\((.*?)\);'
callbacks = re.findall(callback_pattern, response.text, re.DOTALL)
print(f"Found {len(callbacks)} AF_initDataCallback calls")

# Look for window._ variables
window_vars = re.findall(r'window\._\w+\s*=\s*(\[.*?\]);', response.text[:100000], re.DOTALL)
print(f"Found {len(window_vars)} window._ variables")

# Search for product-related JSON
if 'price' in response.text.lower():
    print("\n✅ Response contains 'price' text")
    
    # Find context around price
    price_matches = list(re.finditer(r'price', response.text.lower()))[:3]
    for match in price_matches:
        start = max(0, match.start() - 100)
        end = min(len(response.text), match.end() + 100)
        context = response.text[start:end]
        print(f"\nContext around 'price':")
        print(f"...{context}...")

# Check if it's actually loading data via XHR
if 'async' in response.text.lower():
    print("\n⚠️  Page might load products via async requests")
    async_urls = re.findall(r'/async/[^"\'<>]+', response.text)[:5]
    if async_urls:
        print(f"Found {len(async_urls)} async URLs:")
        for url in async_urls:
            print(f"  https://www.google.com{url}")
