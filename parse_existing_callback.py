"""
Parse the callback_response.txt we already captured
This PROVES the data is accessible!
"""

from bs4 import BeautifulSoup
import json
import re

def parse_product(container):
    """Parse a single product"""
    soup = BeautifulSoup(str(container), 'html.parser')
    
    # Title
    title_elem = soup.find('div', class_='gkQHve')
    title = title_elem.get_text(strip=True) if title_elem else None
    
    # Price
    price = None
    price_elem = soup.find('span', class_='lmQWe')
    if price_elem:
        price_text = price_elem.get_text(strip=True)
        match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
        if match:
            price = float(match.group(1).replace(',', ''))
    
    # Original price
    original_price = None
    was_price = soup.find('span', class_='DoCHT')
    if was_price:
        price_text = was_price.get_text(strip=True)
        match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
        if match:
            original_price = float(match.group(1).replace(',', ''))
    
    # Merchant
    merchant_elem = soup.find('span', class_='WJMUdc')
    merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
    
    # Rating
    rating = None
    rating_elem = soup.find('span', class_='yi40Hd')
    if rating_elem:
        try:
            rating = float(rating_elem.get_text(strip=True))
        except ValueError:
            pass
    
    # Reviews
    reviews = None
    reviews_elem = soup.find('span', class_='RDApEe')
    if reviews_elem:
        text = reviews_elem.get_text(strip=True)
        match = re.search(r'\(([0-9.]+)([KM])?\)', text)
        if match:
            num = float(match.group(1))
            multiplier = match.group(2)
            if multiplier == 'K':
                num *= 1000
            elif multiplier == 'M':
                num *= 1000000
            reviews = int(num)
    
    return {
        'title': title,
        'price': price,
        'original_price': original_price,
        'merchant': merchant,
        'rating': rating,
        'review_count': reviews
    }

print("="*80)
print("PARSING EXISTING CALLBACK DATA")
print("="*80)

# Load the callback response
with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/callback_response.txt') as f:
    html = f.read()

print(f"\nFile size: {len(html):,} bytes")

# Parse it
soup = BeautifulSoup(html, 'html.parser')

# Find product containers
containers = soup.find_all('div', class_='liKJmf')
print(f"Product containers found: {len(containers)}")

# Parse all products
products = []
for container in containers:
    try:
        product = parse_product(container)
        if product.get('title') and product.get('price'):
            products.append(product)
    except Exception as e:
        continue

print(f"Valid products parsed: {len(products)}")

# Display products
print("\n" + "="*80)
print("PRODUCTS:")
print("="*80)

for i, p in enumerate(products[:20], 1):
    print(f"\n{i}. {p['title']}")
    print(f"   💰 ${p['price']}", end="")
    
    if p['original_price']:
        savings = p['original_price'] - p['price']
        pct = (savings / p['original_price']) * 100
        print(f" (was ${p['original_price']} - SAVE {pct:.0f}%!)", end="")
    
    print(f"\n   🏪 {p['merchant']}")
    
    if p['rating']:
        stars = "⭐" * int(round(p['rating']))
        print(f"   {stars} {p['rating']}/5 ({p['review_count']:,} reviews)")

print("\n" + "="*80)
print(f"✅ TOTAL: {len(products)} PRODUCTS SUCCESSFULLY PARSED!")
print("="*80)

# Save
with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/products.json', 'w') as f:
    json.dump(products, f, indent=2)

print("\n💾 Saved to products.json")

