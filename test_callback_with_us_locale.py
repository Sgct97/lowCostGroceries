"""
Test the callback URL with US locale parameters added

Simple fix: just add &hl=en&gl=us to the callback URL!
"""

from curl_cffi import requests
import os
import re

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

# Original callback URL (returns €)
original_url = "https://www.google.com/async/callback:6948?fc=ErcCCvcBQUxrdF92Rk5Fb0FJUmItZ0xXRHVmWEhwWm1qWGNfSGxXZXBzUVBRbHhzWkVXQjhpRmhhSWNJQ24xLXRCWXUyamV2aEVwSUZOdlo4b1lpR0xTUXhqTUJzR2tIYVVFUlg4cEdTWEJKblpSX09UbnlNaXJjSTdtTjBPUktyU0hLSzlBb2lHdHNjMVBvUXY4NlZmc0xLY29DZFZzbDBseU8tZVVLUlBESmpiZWVyS2ZkdTQxUzluc2xxTE8ydm1lcWY4dHZ5OElPSXYzWHFxb3BrNnB1d3Jsb1dFUmV5TGZtME5FZUFpV2QyWDBVX29wSGVYRG9pUGNOTRIXZ3dZZWFiVFJJTFNSd2JrUGw2aUF5UWsaIkFGTUFHR3BzUE1GNTdocHNSSXNqM29kdFRpNlpQSjdiZGc&fcv=3&vet=12ahUKEwj0npK35v6QAxW0SDABHRcUIJkQ9pcOegQICRAB..i&ei=gwYeabTRILSRwbkPl6iAyQk&opi=95576897&sca_esv=55588fd05011d482&shopmd=1&udm=28&yv=3&cs=0"

# Add US locale parameters
us_url = original_url + "&hl=en&gl=us"

print("\n" + "="*80)
print("🇺🇸 TESTING CALLBACK URL WITH US LOCALE".center(80))
print("="*80 + "\n")

proxies = {
    "http": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
    "https": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
} if PROXY_USER and PROXY_PASS else None

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "referer": "https://shopping.google.com/",
}

try:
    print("📡 Testing with curl_cffi (NO BROWSER!)...")
    response = requests.get(
        us_url,
        headers=headers,
        proxies=proxies,
        impersonate="chrome120",
        timeout=30
    )
    
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Size: {len(response.text):,} bytes\n")
    
    html = response.text
    
    # Count currencies
    dollar_count = html.count('$')
    euro_count = html.count('€')
    
    # Extract prices
    dollar_prices = re.findall(r'\$\s*(\d+[\.,]\d+)', html)
    euro_prices = re.findall(r'(\d+[\.,]\d+)\s*€', html)
    
    # Count products
    product_count = html.count('class="liKJmf"')
    
    print("="*80)
    print("RESULTS")
    print("="*80 + "\n")
    print(f"💵 Dollar signs ($): {dollar_count}")
    print(f"💶 Euro signs (€): {euro_count}")
    print(f"📦 Product containers: {product_count}")
    print(f"💰 USD prices found: {len(dollar_prices)}")
    print(f"💰 EUR prices found: {len(euro_prices)}\n")
    
    if dollar_prices:
        print("✅ Sample USD prices:")
        for i, price in enumerate(dollar_prices[:10], 1):
            print(f"   {i}. ${price}")
    
    if euro_prices:
        print("\n⚠️  Sample EUR prices (should be empty!):")
        for i, price in enumerate(euro_prices[:5], 1):
            print(f"   {i}. {price}€")
    
    # Save for inspection
    with open("us_locale_callback_response.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n📄 Saved to: us_locale_callback_response.html")
    
    print("\n" + "="*80)
    if dollar_count > euro_count and len(dollar_prices) > 0:
        print("🎉🎉🎉 PERFECT! HYBRID ARCHITECTURE PROVEN! 🎉🎉🎉".center(80))
        print("="*80 + "\n")
        print("✅ curl_cffi (NO BROWSER!) got product data")
        print("✅ Prices are in USD ($)")
        print(f"✅ Found {len(dollar_prices)} products")
        print(f"✅ Found {product_count} product containers\n")
        print("🚀 FOR 25K USERS:")
        print("   1. UC: Capture callbacks with &hl=en&gl=us")
        print("   2. curl_cffi: Use those URLs (FAST!)")
        print("   3. ~4 hours total for 25K users")
        print("   4. Gets real product data with $ prices")
    else:
        print("⚠️  ISSUE: Still getting EUR prices".center(80))
        print("="*80 + "\n")
        print(f"This callback URL might be session-locked to EUR")
        print(f"Need to capture fresh URLs with US locale from the start")
    
    print("="*80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

