import sys
sys.path.append('backend')
import requests
from bs4 import BeautifulSoup

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"
proxies = {'http': proxy, 'https': proxy}

session = requests.Session()
session.proxies = proxies
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
})

print("Step 1: Accepting Google consent...")
# Go to Google first to get consent cookies
consent_response = session.get("https://www.google.com", timeout=20)
print(f"  Status: {consent_response.status_code}")

# Now try shopping search
print("\nStep 2: Searching Google Shopping...")
search_url = "https://www.google.com/search?q=milk&tbm=shop&gl=us&hl=en"
response = session.get(search_url, timeout=20)

print(f"  Status: {response.status_code}")
print(f"  Size: {len(response.text):,} bytes")

soup = BeautifulSoup(response.text, 'html.parser')
products = soup.find_all('div', class_='liKJmf')

print(f"\n✅ Products found: {len(products)}")

if len(products) > 0:
    print("\n🎉 IT WORKS!\n")
    for i in range(min(5, len(products))):
        title_elem = soup.find_all('div', class_='gkQHve')[i]
        price_elem = soup.find_all('span', class_='lmQWe')[i] if i < len(soup.find_all('span', class_='lmQWe')) else None
        
        title = title_elem.get_text() if title_elem else "N/A"
        price = price_elem.get_text() if price_elem else "N/A"
        
        print(f"{i+1}. {title} - {price}")
else:
    title = soup.find('title')
    print(f"❌ Page: {title.get_text() if title else 'Unknown'}")
    
    # Try without tbm=shop
    print("\nStep 3: Trying regular search...")
    regular_url = "https://www.google.com/search?q=milk+grocery+price"
    regular_response = session.get(regular_url, timeout=20)
    
    if '$' in regular_response.text:
        print("✅ Regular search has prices!")
    else:
        print("❌ Still blocked")
