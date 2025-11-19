from curl_cffi import requests
from bs4 import BeautifulSoup

USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

proxy_url = f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"
proxies = {"http": proxy_url, "https": proxy_url}

# The callback URL YOU captured that WORKS
callback_url = "https://www.google.com/async/callback:6948?fc=EvcCCrcCQUxrdF92R2wzYmNoR3dyM3FNS0pJUU1pdUU1M0x4b195X2pzTUMwcy1Qekc4N0RGbXEyYnozQk9RdEZBMml2WWpNM2VBakVRM2FVSXU0eVc1TGpRazBlNVA2S1JYRXREYmlzVTRzcWRvR3hDYkVqam9mMTZ6eDFIVWFzZktGNVJueWgtelFmdjl2OS1BZXd6QkdYV3kzNEJzUzIzeVhpUnBjZGJ3d0hvYmtyMmlvNS1qUU1VZXZVMTROSWZoYTU0NjBnY3pnNnBtVENTR3NHc1N1OThqWEo1elpTRmNsa1kzYjR3ZXhLUEt3MzNmN01NR3BIR0laMGlMQTlBTlBRMTZMN000eERnelJzQkdWYnZRa2k4LXhub1R6RERwSUk1MEVvYmx4LUh2OXRQTnMzbWxkaFFFbUUSF1JHa1dhZURWTXRiVjVOb1A0NVNhOEFFGiJBRk1BR0dxNXQybmRwVldHQ3BWenl0blBqbDJYejdYUGRB&fcv=3"

print("="*80)
print("TESTING CALLBACK ENDPOINT WITH curl_cffi + OXYLABS")
print("="*80)

response = requests.get(
    callback_url,
    proxies=proxies,
    impersonate="chrome120",
    timeout=30
)

print(f"\n✅ Status: {response.status_code}")
print(f"✅ Size: {len(response.text):,} bytes")

# Remove XSSI
content = response.text
if content.startswith(')]}\''):
    content = content[4:]
    print("✅ Removed XSSI protection")

# Parse
soup = BeautifulSoup(content, 'html.parser')
products = soup.find_all('div', class_='liKJmf')

print(f"✅ Products found: {len(products)}")

if len(products) > 0:
    print("\n🎉 CALLBACK ENDPOINT WORKS!\n")
    
    for i in range(min(10, len(products))):
        title_elem = soup.find_all('div', class_='gkQHve')[i] if i < len(soup.find_all('div', class_='gkQHve')) else None
        price_elem = soup.find_all('span', class_='lmQWe')[i] if i < len(soup.find_all('span', class_='lmQWe')) else None
        merchant_elem = soup.find_all('span', class_='WJMUdc')[i] if i < len(soup.find_all('span', class_='WJMUdc')) else None
        
        title = title_elem.get_text() if title_elem else "N/A"
        price = price_elem.get_text() if price_elem else "N/A"
        merchant = merchant_elem.get_text() if merchant_elem else "N/A"
        
        print(f"{i+1}. {title}")
        print(f"   💰 {price} @ {merchant}\n")
    
    print("="*80)
    print("✅ SOLUTION: Use callback endpoint approach!")
    print("="*80)
else:
    print("\n❌ Callback expired or blocked")
