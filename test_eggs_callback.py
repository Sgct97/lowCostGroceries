import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/backend')

from token_service import TokenService  
from proxy_manager import ProxyPool, Proxy
import requests
import re
import os
import time

# Load proxy credentials from environment
PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.environ.get("PROXY_USER")
PROXY_PASS = os.environ.get("PROXY_PASS")

if not PROXY_USER or not PROXY_PASS:
    print("❌ PROXY_USER and PROXY_PASS environment variables required!")
    sys.exit(1)

proxies_config = [
    Proxy(host=PROXY_HOST, port=int(PROXY_PORT), username=PROXY_USER, password=PROXY_PASS, label="oxylabs_isp")
]

proxy_pool = ProxyPool(proxies=proxies_config)
token_service = TokenService(proxy_pool=proxy_pool)

print("=" * 80)
print("CAPTURING CALLBACK FOR: fresh eggs")
print("=" * 80)

callback_url = token_service.capture_callback_url(region="US", test_query="fresh eggs")

if callback_url:
    print(f"✅ Captured: {callback_url[:100]}...")
    
    # Save it
    with open("eggs_callback_url.txt", "w") as f:
        f.write(callback_url)
    
    # Test it immediately
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }
    
    print("\nTesting callback with plain requests...")
    response = requests.get(callback_url, headers=headers, timeout=15)
    titles = re.findall(r'<div class="gkQHve[^>]*>([^<]+)</div>', response.text)
    prices = re.findall(r'aria-label="Current Price: \\$([0-9]+\.[0-9]{2})', response.text)
    
    print(f"\nProducts returned:")
    for i, title in enumerate(titles[:15], 1):
        egg_marker = "🥚" if "egg" in title.lower() else "  "
        print(f"{i:2d}. {egg_marker} {title}")
    
    egg_count = sum(1 for t in titles if "egg" in t.lower())
    milk_count = sum(1 for t in titles if "milk" in t.lower() or "almond" in t.lower())
    
    print(f"\n" + "=" * 80)
    print(f"Egg products: {egg_count}/{len(titles)}")
    print(f"Milk products: {milk_count}/{len(titles)}")
    print(f"Total prices: {len(prices)}")
    print("=" * 80)
    
    if egg_count > len(titles) // 2:
        print("\n✅ SUCCESS! This callback returns EGG products!")
        print("✅ WE CAN CACHE CALLBACKS PER PRODUCT TYPE!")
    elif egg_count > 0:
        print(f"\n⚠️  MIXED RESULTS: {egg_count} eggs + {milk_count} milk products")
    else:
        print("\n❌ FAIL! This callback still returns MILK products only!")
else:
    print("❌ Failed to capture callback")

