from curl_cffi import requests
import re

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="120", "Chromium";v="120", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1"
}

print("Testing WITH full headers:")

response = requests.get(
    "https://www.google.com/search?udm=28&q=milk&hl=en&gl=us",
    headers=headers,
    proxies={"http": PROXY, "https": PROXY},
    impersonate="chrome120",
    timeout=30,
    allow_redirects=True
)

print(f"Status: {response.status_code}")
print(f"Size: {len(response.text):,}")
print(f"Final URL: {response.url}")

# Check for blocks
if "antes de" in response.text.lower() or "before you continue" in response.text.lower():
    print("❌ CONSENT PAGE")
else:
    print("✅ NO CONSENT!")

# Look for callback
callbacks = re.findall(r'(/async/callback:\d+\?[^"\'<>\s]+)', response.text)
print(f"Callbacks: {len(callbacks)}")

# Look for product data
prices = re.findall(r'\$\d+', response.text)
print(f"Price patterns: {len(prices)}")

with open('oxylabs_v2.html', 'w') as f:
    f.write(response.text)
print("Saved to: oxylabs_v2.html")
