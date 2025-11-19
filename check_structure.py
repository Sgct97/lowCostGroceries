from curl_cffi import requests
from bs4 import BeautifulSoup
import re

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy_url = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"
proxies = {"http": proxy_url, "https": proxy_url}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}

response = requests.get(
    "https://www.google.com/search?q=milk&tbm=shop",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

# Save for inspection
with open('curl_cffi_response.html', 'w') as f:
    f.write(response.text)

soup = BeautifulSoup(response.text, 'html.parser')

# Check for ANY prices
prices_with_dollar = soup.find_all(string=re.compile(r'\$\d+'))
print(f"Elements with $ sign: {len(prices_with_dollar)}")
if len(prices_with_dollar) > 0:
    print("Sample prices found:")
    for p in prices_with_dollar[:5]:
        print(f"  {p.strip()[:50]}")

# Look for common shopping classes
shopping_classes = ['sh-dgr__content', 'sh-dlr__list-result', 'mnr-c', 'Qlx7of']
for cls in shopping_classes:
    elements = soup.find_all(class_=cls)
    if len(elements) > 0:
        print(f"\n✅ Found class '{cls}': {len(elements)} elements")

# Check if it's the mobile version
if 'shopping/m/' in response.text or 'viewport' in response.text:
    print("\n📱 Might be mobile version")

# Look for product data in scripts
scripts = soup.find_all('script')
for script in scripts:
    if script.string and ('price' in script.string.lower() or 'product' in script.string.lower()):
        print(f"\n✅ Found product data in script tag ({len(script.string)} chars)")
        break
