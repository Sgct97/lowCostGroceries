from curl_cffi import requests

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy_url = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"
proxies = {"http": proxy_url, "https": proxy_url}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
}

print("Testing different Google Shopping URLs:\n")

# Test 1: shopping.google.com
print("1. shopping.google.com:")
response1 = requests.get(
    "https://shopping.google.com/search?q=milk",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)
print(f"   Status: {response1.status_code}, Size: {len(response1.text):,}")
print(f"   Final URL: {response1.url}")
print(f"   Has products? {'$' in response1.text}")

# Test 2: www.google.com with tbm=shop
print("\n2. www.google.com with tbm=shop:")
response2 = requests.get(
    "https://www.google.com/search?q=milk&tbm=shop",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)
print(f"   Status: {response2.status_code}, Size: {len(response2.text):,}")
print(f"   Final URL: {response2.url}")
print(f"   Has products? {'$' in response2.text}")

# Test 3: With udm=28 parameter
print("\n3. www.google.com with tbm=shop&udm=28:")
response3 = requests.get(
    "https://www.google.com/search?q=milk&tbm=shop&udm=28",
    headers=headers,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)
print(f"   Status: {response3.status_code}, Size: {len(response3.text):,}")
print(f"   Final URL: {response3.url}")
print(f"   Has products? {'$' in response3.text}")

# Check which one actually has product data
from bs4 import BeautifulSoup
for i, resp in enumerate([response1, response2, response3], 1):
    soup = BeautifulSoup(resp.text, 'html.parser')
    products = soup.find_all('div', class_='liKJmf')
    if len(products) > 0:
        print(f"\n✅ Test {i} found {len(products)} products!")
