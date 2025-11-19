import requests
import re
import json

url = "https://shopping.google.com/search"
params = {'q': 'milk'}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

response = requests.get(url, params=params, headers=headers, timeout=15)
html = response.text

print(f"Response size: {len(html):,} bytes\n")

# Look for AF_initDataCallback
callbacks = re.findall(r'AF_initDataCallback\((.*?)\);', html, re.DOTALL)
print(f"AF_initDataCallback calls: {len(callbacks)}")

if callbacks:
    for i, cb in enumerate(callbacks[:10]):
        if ('price' in cb.lower() or 'product' in cb.lower()) and len(cb) > 500:
            print(f"\n✅ FOUND PRODUCT DATA IN CALLBACK {i}!")
            print(f"Length: {len(cb):,} chars")
            print(f"Sample: {cb[:500]}")
            
            with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/product_callback_{i}.txt', 'w') as f:
                f.write(cb)
            print(f"💾 Saved to product_callback_{i}.txt")
            break
else:
    print("No AF_initDataCallback found")

# Look for window variables
window_vars = re.findall(r'(window\.\w+\s*=\s*\[.*?\]);', html[:100000], re.DOTALL)
print(f"\nWindow variables: {len(window_vars)}")
if window_vars:
    for i, var in enumerate(window_vars[:3]):
        if 'price' in var.lower() or 'product' in var.lower():
            print(f"✅ Found product data in window var!")
            print(f"Sample: {var[:300]}")
