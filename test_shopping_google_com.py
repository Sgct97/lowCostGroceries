from curl_cffi import requests
import re

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

# Try the dedicated shopping.google.com domain
urls = [
    "https://shopping.google.com/search?q=milk",
    "https://www.google.com/search?tbm=shop&q=milk",
]

for url in urls:
    print(f"\nTesting: {url}")
    response = requests.get(
        url,
        headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
        proxies={"http": PROXY, "https": PROXY},
        impersonate="chrome120",
        timeout=30
    )
    
    print(f"  Status: {response.status_code}")
    print(f"  Size: {len(response.text):,}")
    
    # Check for product indicators
    has_prices = len(re.findall(r'\$\d+', response.text))
    has_milk = "milk" in response.text.lower()
    has_challenge = "trouble accessing" in response.text.lower()
    
    print(f"  Prices: {has_prices}, Has 'milk': {has_milk}, Challenge: {has_challenge}")
