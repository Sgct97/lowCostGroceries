from curl_cffi import requests
import re

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

# Make initial request
print("Making initial request to Google Shopping...")
response = requests.get(
    "https://www.google.com/search?udm=28&q=macbook+pro",
    headers={
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
    },
    proxies={"http": PROXY, "https": PROXY},
    impersonate="chrome120",
    allow_redirects=True
)

html = response.text

# Save it
with open('final_test.html', 'w') as f:
    f.write(html)

print(f"Status: {response.status_code}")
print(f"Length: {len(html):,} bytes")
print(f"Final URL: {response.url}")

# Look for EVERYTHING related to callbacks
callback_patterns = [
    (r'/async/callback[^"\'<>\s]*', 'Direct callback URL'),
    (r'callback:\d+', 'Callback ID'),
    (r'["\']fc["\']\s*[:=]\s*["\']([^"\'&\s]+)', 'fc token (quoted)'),
    (r'\bfc[=:]([^&\s"\'<>]+)', 'fc token (unquoted)'),
    (r'["\']ei["\']\s*[:=]\s*["\']([^"\'&\s]+)', 'ei token (quoted)'),
    (r'\bei[=:]([^&\s"\'<>]+)', 'ei token (unquoted)'),
    (r'async["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', 'async param'),
]

print("\n" + "="*80)
print("🔍 SEARCHING FOR CALLBACK CLUES:")
print("="*80)

found_tokens = {}

for pattern, description in callback_patterns:
    matches = re.findall(pattern, html, re.IGNORECASE)
    if matches:
        print(f"\n✅ Found {description}: {pattern}")
        unique_matches = list(set(matches))[:5]
        for match in unique_matches:
            print(f"   {match[:100]}")
        found_tokens[description] = unique_matches[0] if unique_matches else None

# Look for product data
print("\n" + "="*80)
print("🔍 PRODUCT DATA CHECK:")
print("="*80)

product_indicators = ['MacBook', 'macbook', '$1,', 'apple', 'price', 'product']
for indicator in product_indicators:
    count = html.lower().count(indicator.lower())
    print(f"  '{indicator}': {count} mentions")
    
    if count > 0 and count < 10:  # Show context if not too many
        idx = html.lower().find(indicator.lower())
        context = html[max(0, idx-100):idx+100]
        print(f"     Context: ...{context}...")

# Try to construct a callback URL if we found tokens
print("\n" + "="*80)
print("🔧 CALLBACK URL CONSTRUCTION ATTEMPT:")
print("="*80)

if 'fc token (unquoted)' in found_tokens and 'ei token (unquoted)' in found_tokens:
    fc = found_tokens['fc token (unquoted)']
    ei = found_tokens['ei token (unquoted)']
    
    # Try to construct callback
    callback_url = f"https://www.google.com/async/callback?fc={fc}&ei={ei}&udm=28&yv=3&cs=0&async=_fmt:prog"
    
    print(f"✅ Constructed callback URL:")
    print(f"   {callback_url}")
    
    print(f"\n🧪 Testing constructed callback URL...")
    try:
        callback_response = requests.get(
            callback_url,
            headers=headers,
            proxies={"http": PROXY, "https": PROXY},
            impersonate="chrome120",
            timeout=10
        )
        
        print(f"   Status: {callback_response.status_code}")
        print(f"   Size: {len(callback_response.text):,} bytes")
        
        # Check for product data
        if 'MacBook' in callback_response.text or 'liKJmf' in callback_response.text:
            print(f"   ✅✅✅ PRODUCT DATA FOUND IN CALLBACK!")
            with open('constructed_callback.html', 'w') as f:
                f.write(callback_response.text)
            print(f"   Saved to: constructed_callback.html")
        else:
            print(f"   ❌ No product data in callback response")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print("❌ Could not find both fc and ei tokens")
    print(f"   Found: {list(found_tokens.keys())}")

print("\n" + "="*80)
print("FINAL TEST COMPLETE")
print("="*80)
