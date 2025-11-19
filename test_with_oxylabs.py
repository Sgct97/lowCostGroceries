from curl_cffi import requests
import re

# Oxylabs config
PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

print("Testing curl_cffi WITH Oxylabs proxy:")

response = requests.get(
    "https://www.google.com/search?udm=28&q=milk",
    headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    proxies={"http": PROXY, "https": PROXY},
    impersonate="chrome120",
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"Size: {len(response.text):,}")

# Check for blocks
if "If you're having trouble" in response.text:
    print("❌ BLOCKED: Challenge page")
elif "before you continue" in response.text.lower():
    print("❌ BLOCKED: Consent page")
else:
    print("✅ NO BLOCK!")

# Look for callback URL
callback_urls = re.findall(r'(/async/callback:\d+\?[^"\'<>\s]+)', response.text)
print(f"\nCallback URLs found: {len(callback_urls)}")
if callback_urls:
    print(f"First callback: {callback_urls[0][:100]}...")

# Check for products
if "milk" in response.text.lower():
    print("✅ Found 'milk'")

# Save
with open('oxylabs_test.html', 'w') as f:
    f.write(response.text)
print("\nSaved to: oxylabs_test.html")
