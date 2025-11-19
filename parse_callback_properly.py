"""
Parse the callback response properly with BeautifulSoup
"""

from bs4 import BeautifulSoup

with open("callback_response_from_curl.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all product containers
products = []
product_containers = soup.find_all('div', class_='liKJmf')

print(f"\n🔍 Found {len(product_containers)} product containers\n")

for i, container in enumerate(product_containers[:10], 1):  # First 10
    # Title
    title_elem = container.find('div', class_='gkQHve')
    title = title_elem.get_text(strip=True) if title_elem else 'N/A'
    
    # Price - look for the lmQWe class
    price_elem = container.find('span', class_='lmQWe')
    price = price_elem.get_text(strip=True) if price_elem else 'N/A'
    
    # Merchant
    merchant_elem = container.find('span', class_='WJMUdc')
    merchant = merchant_elem.get_text(strip=True) if merchant_elem else 'N/A'
    
    print(f"{i}. {title[:60]}...")
    print(f"   💰 {price}")
    print(f"   🏪 {merchant}")
    print()
    
    products.append({
        'title': title,
        'price': price,
        'merchant': merchant
    })

print("="*80)
print(f"✅ SUCCESSFULLY PARSED {len(products)} PRODUCTS WITH PRICES!")
print("="*80)

