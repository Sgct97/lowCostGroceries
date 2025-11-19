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

print("="*80)
print("TESTING www.google.com/search?tbm=shop")
print("="*80)

response = requests.get(
    "https://www.google.com/search?q=milk&tbm=shop",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

print(f"\n✅ Response: {len(response.text):,} bytes")
print(f"✅ Final URL: {response.url}")

# Check for prices
if '$' in response.text:
    print("✅ Contains $ signs")
    # Find first few dollar signs with context
    matches = re.findall(r'.{0,50}\$\d+\.?\d*.{0,50}', response.text)[:5]
    print("\nFirst 5 price occurrences:")
    for m in matches:
        print(f"  ...{m.strip()}...")
else:
    print("❌ No $ signs found")

# Try parsing
soup = BeautifulSoup(response.text, 'html.parser')
products = soup.find_all('div', class_='liKJmf')
print(f"\n✅ Product containers found: {len(products)}")

if len(products) > 0:
    print("\n🎉 SUCCESS! Parsing products:\n")
    for i in range(min(5, len(products))):
        title_elem = soup.find_all('div', class_='gkQHve')[i] if i < len(soup.find_all('div', class_='gkQHve')) else None
        price_elem = soup.find_all('span', class_='lmQWe')[i] if i < len(soup.find_all('span', class_='lmQWe')) else None
        merchant_elem = soup.find_all('span', class_='WJMUdc')[i] if i < len(soup.find_all('span', class_='WJMUdc')) else None
        
        title = title_elem.get_text() if title_elem else "N/A"
        price = price_elem.get_text() if price_elem else "N/A"
        merchant = merchant_elem.get_text() if merchant_elem else "N/A"
        
        print(f"{i+1}. {title}")
        print(f"   💰 {price} @ {merchant}\n")
