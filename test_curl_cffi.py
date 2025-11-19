from curl_cffi import requests
from bs4 import BeautifulSoup

# Your Oxylabs credentials
USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"
PORT = "8001"

proxy_url = f"http://{USERNAME}:{PASSWORD}@{HOST}:{PORT}"
proxies = {"http": proxy_url, "https": proxy_url}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

print("="*80)
print("TESTING curl_cffi WITH OXYLABS")
print("="*80)

# THE MAGIC: impersonate="chrome120"
response = requests.get(
    "https://www.google.com/search?q=milk&tbm=shop&gl=us&hl=en",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

print(f"\n✅ Status: {response.status_code}")
print(f"✅ Size: {len(response.text):,} bytes")

# Check for consent page
if "Before you continue" in response.text:
    print("\n❌ FAILED: Still got consent page")
else:
    print("\n✅ SUCCESS: Bypassed consent!")

# Parse products
soup = BeautifulSoup(response.text, 'html.parser')
products = soup.find_all('div', class_='liKJmf')

print(f"✅ Products found: {len(products)}")

if len(products) > 0:
    print("\n🎉 IT WORKS! Here are the products:\n")
    
    titles = soup.find_all('div', class_='gkQHve')
    prices = soup.find_all('span', class_='lmQWe')
    merchants = soup.find_all('span', class_='WJMUdc')
    
    for i in range(min(10, len(titles))):
        title = titles[i].get_text() if i < len(titles) else "N/A"
        price = prices[i].get_text() if i < len(prices) else "N/A"
        merchant = merchants[i].get_text() if i < len(merchants) else "N/A"
        
        print(f"{i+1}. {title}")
        print(f"   💰 {price} @ {merchant}\n")
else:
    print("\n❌ No products found")
    print("First 300 chars of response:")
    print(response.text[:300])
