from curl_cffi import requests

print("Testing curl_cffi WITHOUT proxy:")

response = requests.get(
    "https://www.google.com/search?udm=28&q=milk",
    headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    impersonate="chrome120",
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"Size: {len(response.text):,}")

# Check for challenge
if "If you're having trouble" in response.text or "before you continue" in response.text.lower():
    print("❌ BLOCKED: Challenge/consent page")
else:
    print("✅ NO BLOCK")

# Check for products
if "milk" in response.text.lower():
    print("✅ Found 'milk'")
else:
    print("❌ No 'milk'")

# Save
with open('no_proxy_curl_test.html', 'w') as f:
    f.write(response.text)
print("Saved to: no_proxy_curl_test.html")
