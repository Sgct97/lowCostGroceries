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
print("SCRAPING GOOGLE SHOPPING WITH curl_cffi + OXYLABS")
print("="*80)

response = requests.get(
    "https://shopping.google.com/search?q=milk",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

print(f"\n✅ Got response: {len(response.text):,} bytes")

soup = BeautifulSoup(response.text, 'html.parser')

# Try different product container classes
product_containers = soup.find_all('div', class_='liKJmf')
print(f"✅ Product containers (.liKJmf): {len(product_containers)}")

if len(product_containers) > 0:
    print("\n🎉 PRODUCTS FOUND!\n")
    
    for i, container in enumerate(product_containers[:10], 1):
        # Title
        title_elem = container.find('div', class_='gkQHve')
        title = title_elem.get_text(strip=True) if title_elem else "N/A"
        
        # Price
        price_elem = container.find('span', class_='lmQWe')
        price = price_elem.get_text(strip=True) if price_elem else "N/A"
        
        # Merchant
        merchant_elem = container.find('span', class_='WJMUdc')
        merchant = merchant_elem.get_text(strip=True) if merchant_elem else "N/A"
        
        print(f"{i}. {title}")
        print(f"   💰 {price} @ {merchant}\n")
else:
    print("\n❌ No products in .liKJmf containers")
    print("Trying alternate selectors...")
    
    # Save HTML for inspection
    with open('shopping_response.html', 'w') as f:
        f.write(response.text)
    print("Saved to shopping_response.html for inspection")
