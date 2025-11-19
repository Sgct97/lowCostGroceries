from curl_cffi import requests
import re

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

session = requests.Session()

# Full browser headers
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "sec-ch-ua": '"Google Chrome";v="120", "Chromium";v="120", "Not?A_Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Step 1: Loading shopping.google.com homepage...")
response = session.get(
    "https://shopping.google.com",
    headers=headers,
    proxies={"http": PROXY, "https": PROXY},
    impersonate="chrome120"
)
print(f"  Status: {response.status_code}, Size: {len(response.text):,}")

print("\nStep 2: Searching for 'milk'...")
response = session.get(
    "https://shopping.google.com/search?q=milk&hl=en",
    headers=headers,
    proxies={"http": PROXY, "https": PROXY},
    impersonate="chrome120"
)

print(f"  Status: {response.status_code}")
print(f"  Size: {len(response.text):,}")
print(f"  URL: {response.url}")

# Save
with open('shopping_session_test.html', 'w') as f:
    f.write(response.text)

# Analyze
prices = re.findall(r'\$\d+', response.text)
callbacks = re.findall(r'/async/callback:\d+\?[^"\'<>\s]+', response.text)
json_blocks = re.findall(r'\{[^}]{100,}\}', response.text)

print(f"\n  Prices found: {len(prices)}")
print(f"  Callbacks found: {len(callbacks)}")
print(f"  JSON blocks found: {len(json_blocks)}")

if prices:
    print(f"  Sample prices: {prices[:5]}")

if callbacks:
    print(f"  ✓✓ CALLBACK FOUND: {callbacks[0][:80]}...")

print("\nSaved to: shopping_session_test.html")
