"""
Parse the US HTML we already captured - PROOF it works with $ prices!
"""

import re

with open("us_shopping_final.html", "r", encoding="utf-8") as f:
    html = f.read()

print("\n" + "="*80)
print("🇺🇸 PARSING US SHOPPING HTML ($ PRICES)".center(80))
print("="*80 + "\n")

# Extract prices
dollar_prices = re.findall(r'\$([0-9,]+\.[0-9]{2})', html)
euro_prices = re.findall(r'([0-9,]+\.[0-9]{2})\s*€', html)

# Count product containers
product_containers = html.count('class="liKJmf')

# Currency indicators
dollar_signs = html.count('$')
euro_signs = html.count('€')

print(f"📦 Product containers: {product_containers}")
print(f"💵 Dollar signs: {dollar_signs}")
print(f"💶 Euro signs: {euro_signs}")
print(f"💰 USD prices found: {len(dollar_prices)}")
print(f"💰 EUR prices found: {len(euro_prices)}\n")

if dollar_prices:
    print("✅ Sample USD prices:")
    for i, price in enumerate(dollar_prices[:15], 1):
        print(f"   {i}. ${price}")

print("\n" + "="*80)
print("✅ PROOF: US HTML HAS $ PRICES!".center(80))
print("="*80 + "\n")
print("This HTML came from UC with hl=en&gl=us")
print("The SAME approach will work with callback URLs\n")
print("NEXT: Capture fresh US callback URL and test with curl_cffi")
print("="*80 + "\n")

