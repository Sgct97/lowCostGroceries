import sys
sys.path.append('backend')
import requests
from bs4 import BeautifulSoup

# Try with geo parameter for Oxylabs
USERNAME = "lowCostGroceris_26SVt"
PASSWORD = "AppleID_1234"
HOST = "isp.oxylabs.io"

# Some Oxylabs proxies support geo targeting via special username format
# Try: customer-USERNAME-cc-us:PASSWORD
alt_username = f"customer-{USERNAME}-cc-us"
proxy_us = f"http://{alt_username}:{PASSWORD}@{HOST}:8001"

print("Testing with US geo-targeting...")
try:
    response = requests.get(
        "https://www.google.com/search?q=milk&tbm=shop",
        proxies={'http': proxy_us, 'https': proxy_us},
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=20
    )
    print(f"✅ US geo: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    print(f"Title: {title.get_text() if title else 'None'}")
    
    products = soup.find_all('div', class_='liKJmf')
    print(f"Products: {len(products)}")
    
except Exception as e:
    print(f"❌ US geo failed: {e}")

# If that doesn't work, try session-based approach
print("\nOr try WITHOUT tbm=shop parameter first...")
try:
    session = requests.Session()
    session.proxies = {'http': f"http://{USERNAME}:{PASSWORD}@{HOST}:8001", 
                       'https': f"http://{USERNAME}:{PASSWORD}@{HOST}:8001"}
    
    # Use callback URL directly (our proven method!)
    callback_url = "https://www.google.com/async/callback:6948?fc=EvcCCrcCQUxrdF92R2wzYmNoR3dyM3FNS0pJUU1pdUU1M0x4b195X2pzTUMwcy1Qekc4N0RGbXEyYnozQk9RdEZBMml2WWpNM2VBakVRM2FVSXU0eVc1TGpRazBlNVA2S1JYRXREYmlzVTRzcWRvR3hDYkVqam9mMTZ6eDFIVWFzZktGNVJueWgtelFmdjl2OS1BZXd6QkdYV3kzNEJzUzIzeVhpUnBjZGJ3d0hvYmtyMmlvNS1qUU1VZXZVMTROSWZoYTU0NjBnY3pnNnBtVENTR3NHc1N1OThqWEo1elpTRmNsa1kzYjR3ZXhLUEt3MzNmN01NR3BIR0laMGlMQTlBTlBRMTZMN000eERnelJzQkdWYnZRa2k4LXhub1R6RERwSUk1MEVvYmx4LUh2OXRQTnMzbWxkaFFFbUUSF1JHa1dhZURWTXRiVjVOb1A0NVNhOEFFGiJBRk1BR0dxNXQybmRwVldHQ3BWenl0blBqbDJYejdYUGRB&fcv=3"
    
    print("Trying YOUR captured callback URL with Oxylabs...")
    callback_response = session.get(callback_url, timeout=20)
    
    print(f"✅ Callback: {callback_response.status_code}, {len(callback_response.text):,} bytes")
    
    soup2 = BeautifulSoup(callback_response.text, 'html.parser')
    products2 = soup2.find_all('div', class_='liKJmf')
    
    if len(products2) > 0:
        print(f"🎉 CALLBACK WORKS! {len(products2)} products!")
        for i in range(min(3, len(products2))):
            title = soup2.find_all('div', class_='gkQHve')[i].get_text()
            print(f"  {i+1}. {title}")
    else:
        print("Callback returned data but no products")
        
except Exception as e:
    print(f"❌ Callback failed: {e}")
