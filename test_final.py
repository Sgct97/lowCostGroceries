import sys
sys.path.append('backend')
import requests
from bs4 import BeautifulSoup

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

cookies = {'CONSENT': 'YES+'}

url = "https://www.google.com/search?q=milk&tbm=shop&gl=us&hl=en"

print("Testing Oxylabs (simplified)...")
response = requests.get(
    url, 
    proxies={'http': proxy, 'https': proxy},
    headers=headers,
    cookies=cookies,
    timeout=20
)

print(f"✅ Status: {response.status_code}")
print(f"✅ Size: {len(response.text):,} bytes")

soup = BeautifulSoup(response.text, 'html.parser')
products = soup.find_all('div', class_='liKJmf')

print(f"✅ Products: {len(products)}")

if len(products) > 0:
    print("\n🎉 SUCCESS! Oxylabs working!\n")
    titles = soup.find_all('div', class_='gkQHve')
    prices = soup.find_all('span', class_='lmQWe')
    merchants = soup.find_all('span', class_='WJMUdc')
    
    for i in range(min(5, len(titles))):
        title = titles[i].get_text() if i < len(titles) else "N/A"
        price = prices[i].get_text() if i < len(prices) else "N/A"
        merchant = merchants[i].get_text() if i < len(merchants) else "N/A"
        print(f"{i+1}. {title}")
        print(f"   💰 {price} @ {merchant}\n")
else:
    # Check title
    title = soup.find('title')
    print(f"\nPage title: {title.get_text() if title else 'None'}")
    
    # Check if it's a different structure
    all_divs = soup.find_all('div', class_=True)
    print(f"Total divs with classes: {len(all_divs)}")
    
    # Look for ANY price
    if '$' in response.text:
        print("✅ Found $ signs in page - data is there!")
    else:
        print("❌ No prices found")
