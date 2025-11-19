import sys
sys.path.append('backend')
from proxy_manager import ProxyPool
from scraper import GoogleShoppingScraper

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy_list = [f"{HOST}:8001:{USERNAME}:{PASSWORD}"]
pool = ProxyPool.from_list(proxy_list)
scraper = GoogleShoppingScraper(proxy_pool=pool)

# Get raw response
import requests
proxy = pool.get_next_proxy()
url = "https://www.google.com/search?q=milk&tbm=shop&udm=28"

response = requests.get(url, proxies=proxy.dict, timeout=15)
html = response.text

# Save for inspection
with open('oxylabs_response.html', 'w') as f:
    f.write(html)

print(f"Status: {response.status_code}")
print(f"Size: {len(html)} bytes")
print("\nFirst 500 chars:")
print(html[:500])

# Check for blocks
if 'captcha' in html.lower():
    print("\n🚫 CAPTCHA detected")
elif 'detected unusual traffic' in html.lower():
    print("\n🚫 Bot detection triggered")
elif '<title>Google</title>' in html:
    print("\n✅ Normal Google page (but might be empty)")
else:
    print("\n❓ Unknown response type")
