from curl_cffi import requests
from bs4 import BeautifulSoup
import re

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}

print("Testing WITHOUT proxy (from your local IP):\n")

response = requests.get(
    "https://www.google.com/search?udm=28&q=macbook+pro&hl=en&gl=us",
    headers=headers,
    impersonate="chrome120",
    timeout=30
)

print(f"Status: {response.status_code}")
print(f"Size: {len(response.text):,} bytes")

# Check for products
soup = BeautifulSoup(response.text, 'html.parser')
products = soup.find_all('div', class_='liKJmf')
print(f"Products (.liKJmf): {len(products)}")

# Check for prices
prices = re.findall(r'\$[\d,]+', response.text)
print(f"Price patterns: {len(prices)}")
if prices:
    print(f"Sample: {prices[:5]}")

# Check for "MacBook"
if "MacBook" in response.text:
    print("\n✅ Found 'MacBook'")
else:
    print("\n❌ No 'MacBook' found")

# Save
with open('no_proxy_response.html', 'w') as f:
    f.write(response.text)
print("\nSaved to: no_proxy_response.html")
