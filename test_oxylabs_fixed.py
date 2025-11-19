import sys
sys.path.append('backend')
from proxy_manager import ProxyPool
import requests

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

# Oxylabs with proper headers
proxy = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Add consent cookie
cookies = {
    'CONSENT': 'YES+',
    'SOCS': 'CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg'
}

url = "https://www.google.com/search?q=milk&tbm=shop&udm=28&gl=us&hl=en"

print("Testing Oxylabs with consent cookies...")
response = requests.get(
    url, 
    proxies={'http': proxy, 'https': proxy},
    headers=headers,
    cookies=cookies,
    timeout=20
)

print(f"Status: {response.status_code}")
print(f"Size: {len(response.text)} bytes")

# Check for products
from bs4 import BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')
products = soup.find_all('div', class_='liKJmf')

print(f"Products found: {len(products)}")

if len(products) > 0:
    print("\n✅ SUCCESS! Found products:")
    for i in range(min(3, len(products))):
        title = soup.find_all('div', class_='gkQHve')[i].get_text() if i < len(soup.find_all('div', class_='gkQHve')) else "N/A"
        print(f"  {i+1}. {title}")
else:
    print("\n❌ Still no products. Checking response...")
    print(response.text[:300])
