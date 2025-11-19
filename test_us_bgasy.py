"""
Test the US bgasy URL - this might be the real product data endpoint!
"""

from curl_cffi import requests
import os
import re

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

# US bgasy URL just captured
US_BGASY_URL = "https://www.google.com/async/bgasy?ei=mgweae27IqeDwbkPtLS8wAk&opi=95576897&sca_esv=55588fd05011d482&shopmd=1&udm=28&yv=3&cs=0&async=_fmt:jspb"

print("\n" + "="*80)
print("🇺🇸 TESTING US /async/bgasy URL".center(80))
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
        US_BGASY_URL,
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
    dollar_prices = re.findall(r'\$([0-9,]+\.[0-9]{2})', html)
    euro_prices = re.findall(r'([0-9,]+\.[0-9]{2})\s*€', html)
    
    # Count products (might be in HTML within the response)
    product_count = html.count('liKJmf')
    
    print("="*80)
    print("RESULTS")
    print("="*80 + "\n")
    print(f"💵 Dollar signs ($): {dollar_count}")
    print(f"💶 Euro signs (€): {euro_count}")
    print(f"📦 Product indicators: {product_count}")
    print(f"💰 USD prices found: {len(dollar_prices)}")
    print(f"💰 EUR prices found: {len(euro_prices)}\n")
    
    # Save for inspection
    with open("us_bgasy_response.txt", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📄 Saved to: us_bgasy_response.txt")
    
    # Show first 500 chars
    print(f"\n📋 First 500 chars:")
    print(html[:500])
    
    print("\n" + "="*80)
    if dollar_count > 0 or len(dollar_prices) > 0:
        print("🎉 SUCCESS! bgasy has $ data!".center(80))
        print("="*80 + "\n")
        if dollar_prices:
            print("✅ Sample prices:")
            for i, price in enumerate(dollar_prices[:10], 1):
                print(f"   {i}. ${price}")
    else:
        print("⚠️  No $ prices in bgasy either".center(80))
        print("="*80 + "\n")
        print("The bgasy URL might need additional parameters")
        print("or might be a different type of endpoint")
    
    print("="*80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

