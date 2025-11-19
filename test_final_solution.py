from curl_cffi import requests
import re

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy_url = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"
proxies = {"http": proxy_url, "https": proxy_url}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

print("="*80)
print("FINAL TEST: udm=28 with REGEX parsing")
print("="*80)

# Use udm=28 directly (new format)
response = requests.get(
    "https://www.google.com/search?udm=28&q=milk&hl=en&gl=us",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

print(f"\n✅ Status: {response.status_code}")
print(f"✅ Final URL: {response.url}")
print(f"✅ Response: {len(response.text):,} bytes")

# Save for inspection
with open('udm28_response.html', 'w') as f:
    f.write(response.text)
print("✅ Saved to: udm28_response.html")

# Check for consent
if "Before you continue" in response.text:
    print("\n❌ BLOCKED: Consent page")
    exit()

print("\n✅ Bypassed consent!")

# Look for product data patterns (escaped JSON like Maps)
print("\n" + "="*80)
print("SEARCHING FOR PRODUCT DATA")
print("="*80)

# Test if "milk" appears (product name)
if "milk" in response.text.lower():
    print("✅ Found 'milk' in response")

# Test if prices appear
price_matches = re.findall(r'\$\d+\.?\d*', response.text)
print(f"✅ Found {len(price_matches)} price patterns: {price_matches[:10]}")

# Look for escaped JSON patterns (like Maps scraper)
escaped_price_pattern = r'\\\\"\\$(\d+\.?\d*)\\\\"'
escaped_prices = re.findall(escaped_price_pattern, response.text)
print(f"✅ Escaped prices (\\\\\"$X.XX\\\\\"): {len(escaped_prices)}")

# Look for product titles in escaped JSON
title_pattern = r'\\\\"([A-Za-z0-9 &|\'.-]{10,80})\\\\"'
potential_titles = re.findall(title_pattern, response.text)
print(f"✅ Potential product titles: {len(potential_titles)}")

if len(potential_titles) > 0:
    print("\nFirst 10 potential products:")
    for i, title in enumerate(potential_titles[:10], 1):
        print(f"  {i}. {title}")

# Look for specific product data patterns
print("\n" + "="*80)
print("ANALYZING DATA STRUCTURE")
print("="*80)

# Count occurrences of key terms
terms = ['product', 'price', 'merchant', 'store', 'brand']
for term in terms:
    count = len(re.findall(term, response.text, re.IGNORECASE))
    print(f"  '{term}': {count} occurrences")

# Check if MacBook test (specific product)
print("\n" + "="*80)
print("TESTING WITH SPECIFIC PRODUCT (MacBook)")
print("="*80)

response2 = requests.get(
    "https://www.google.com/search?udm=28&q=macbook+pro&hl=en&gl=us",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

if "MacBook" in response2.text:
    print("✅ Found 'MacBook' in response")
    
    # Find context
    idx = response2.text.find("MacBook")
    context = response2.text[max(0, idx-100):idx+200]
    print(f"\nContext around 'MacBook':")
    print(f"...{context}...")

if "$" in response2.text:
    print("\n✅ Found $ in response")
    # Find first few dollar amounts
    dollars = re.findall(r'\$[\d,]+\.?\d*', response2.text)[:5]
    print(f"First prices: {dollars}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if len(price_matches) > 0 or len(escaped_prices) > 0:
    print("✅ SUCCESS! Product data is in the response")
    print("✅ Next step: Build regex patterns to extract structured data")
else:
    print("❌ No product data found")
    print("❌ May need Playwright for JavaScript rendering")
