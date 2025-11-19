import requests
from bs4 import BeautifulSoup

url = "https://shopping.google.com/search?q=milk"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers, timeout=15)
html = response.text

# Save it
with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/initial_page.html', 'w') as f:
    f.write(html)

print(f"Page size: {len(html):,} bytes")

# Look for products
soup = BeautifulSoup(html, 'html.parser')
products = soup.find_all('div', class_='liKJmf')
print(f"Product containers: {len(products)}")

# Look for prices
prices = soup.find_all(string=lambda text: text and '$' in text)[:10]
print(f"\nFirst 10 price-like elements:")
for p in prices:
    print(f"  {p.strip()[:50]}")
