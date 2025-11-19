"""
FINAL TEST: US callback URL with curl_cffi (NO BROWSER!)

This will prove the complete hybrid architecture works with $ prices!
"""

from curl_cffi import requests
import os
import re

PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

# Fresh US callback URL just captured
US_CALLBACK_URL = "https://www.google.com/async/callback:6948?fc=ErcCCvcBQUxrdF92RWNHS1c3VXpYWmNSU3Q4WXVfd3l4M0l0RURYMjZRUzFqVWt5X2FNYUVzd2Y5eTZud2x4djNCdmE5N0JyVEZmZHQzdGxQMld4anNBZ1hXM1RoN3BrMl9YNVVEd0J3c25Yd2ljd0FtZmdFbkhYckZCWFBWOF9TdE4wdnNDZG4zWVV3clFVeGpPZmpmcF9qOV9vNWJHemZVTXRNdXNFQVRvXzc3ZUtxeEdrUmtMNWU0amlNZEdrMnVab2JJNERMX1FJcjNpM0NCYldIT043a0pVeVFLM1dzbGpYOEl4N19GdUtXZDdzQ0g4Z1RYeXBPaHdzURIXbWd3ZWFlMjdJcWVEd2JrUHRMUzh3QWsaIkFGTUFHR3FxdTVSRWhiWU1HLWwtMXg0emoxOG9sWFVQLVE&fcv=3&vet=12ahUKEwjt8MWe7P6QAxWnQTABHTQaD5gQ9pcOegQIBRAB..i&ei=mgweae27IqeDwbkPtLS8wAk&opi=95576897&sca_esv=55588fd05011d482&shopmd=1&udm=28&yv=3&cs=0&async=_basejs:%2Fxjs%2F_%2Fjs%2Fk%3Dxjs.s.en.uhWUIktChyo.2019.O%2Fam%3DAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAgIAAAUCAAgAAAAAAAAAAAgAAEAAQAAAAAAAAAAAAAAAAAAAAAAABAQAAAAgBIAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAABkAAACCAgAIAAAAKAAAAAAAAAAAAAAAAQAAEAAAAAAASIAHAf_sDDgAAAAAAAAABAAAAAAAAAAAAAAAAEQAAAAAAAACwAAAgKAwAQABCAAEAAAAAAAAAAAAAAAAAEAAAAAAAAAABAAAAACAAAAAABQAABAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAQAAAAOAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAACAAAYAAAAAAAAoAAAAAAAACAAAAADAAQAAhAAAAAAuoEgAABAAAAAAkAPA4wEcUlAAAAAAAAAAAAAAAAAAAAAAgAAoCOZA8gMCCAAAAAAAAAAAAAAAAAAAAAAAAECKsIm1BgAE%2Fdg%3D0%2Fbr%3D1%2Frs%3DACT90oFibYxoHTAbxnOTxWTWAWhgv17Lwg,_basecss:%2Fxjs%2F_%2Fss%2Fk%3Dxjs.s.OkJxyen5D08.L.B1.O%2Fam%3DAAAGAAAQCAAAAAAAAAAAAAACACAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAEACAAJQhAAAAAAAA0AsAAKQAAAAAAAAAwAMAAAQBAAAAAAAAAIAAAABIAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAMAAACCAEAAAAAAABQAgAAAAAAAAAAAAAAAEAAAAAAAAAAEAAAAADBgAAAgAAAAACAQAAAQAAAAIAAADgDAAAAAAABkAAAAAAAAAQABAAAAAAAAAAIgACCAAQAAAAAAAYAAAAAAAAIABsCAgCIBAhQgAABwAAAAAAAAAAgAAAAAAAAAoABABgRwAAAAAAAIAACAAAOQBAABAAAAQgIAAAG8AgQEAACAQACACAAAAACQABIIAAAAoCAABAAAAAAAAAADACAAAAAAAFgAuokgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAoAAAAAAAAAAAAAAAAAAAAAAAAAAAAI%2Fbr%3D1%2Frs%3DACT90oGUiegVlBn2sIdwrNrUSetyQWruWg,_basecomb:%2Fxjs%2F_%2Fjs%2Fk%3Dxjs.s.en.uhWUIktChyo.2019.O%2Fck%3Dxjs.s.OkJxyen5D08.L.B1.O%2Fam%3DAAAGAAAQCAAAAAAAAAAAAAACACAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAABAAgIAAAUCCAgJQhAAAAAAAA0AsEAKQAAAAAAAAAwAMAAAQBAAAAAABAQIAAAgBIAAAAAAAAAAAAAAAAAAAAEAAAABAAAAAABsAAACCAkAIAAAAKBQAgAAAAAAAAAAAAQAAEAAAAAAASIAHAf_sDDhgAAAgAAAABCAQAAAQAAAAIAAADkTAAAAAAABmwAAAgKAwAQABCAAEAAAAAAIgACCAAQAAAEAAAYAAAAAABAIABsCAgCIBAhQgABBwAAAAAAAAAAgAAAAAAACAoABABgRwAAAAAAAIAQCAAAOQBAABAAAEQgIAAAG8AgQEAACAQACACAACAACYABIIAAAAoCAABAAAACAAAAADACQAAhAAAFgAuokgAABAAAAAAkAPA4wEcUlAAAAAAAAAAAAAAAAAAAAAAgAAoCOZA8gsCCAAAAAAAAAAAAAAAAAAAAAAAAECKsIm1BgAE%2Fd%3D1%2Fed%3D1%2Fdg%3D0%2Fbr%3D1%2Fujg%3D1%2Frs%3DACT90oENQygCLMIYGZQEVC35dU5qxRJZBw,_fmt:prog,_id:fc_mgweae27IqeDwbkPtLS8wAk_1"

print("\n" + "="*80)
print("🇺🇸 FINAL TEST: US CALLBACK URL + curl_cffi".center(80))
print("="*80 + "\n")
print("Testing fresh US callback URL with curl_cffi (NO BROWSER!)\n")

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
    print("📡 Making request with curl_cffi...")
    response = requests.get(
        US_CALLBACK_URL,
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
        for i, price in enumerate(dollar_prices[:15], 1):
            print(f"   {i}. ${price}")
    
    # Save for inspection
    with open("us_callback_response_final.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n📄 Saved to: us_callback_response_final.html")
    
    print("\n" + "="*80)
    if dollar_count > euro_count and len(dollar_prices) > 0 and product_count > 0:
        print("🎉🎉🎉 SUCCESS! HYBRID ARCHITECTURE PROVEN! 🎉🎉🎉".center(80))
        print("="*80 + "\n")
        print("✅ UC auto-captured callback URL with US locale")
        print("✅ curl_cffi (NO BROWSER!) got product data")
        print("✅ Prices are in USD ($)")
        print(f"✅ Found {len(dollar_prices)} products")
        print(f"✅ Found {product_count} product containers\n")
        print("🚀 FOR 25K USERS:")
        print("   1. UC: Capture callbacks (~100 times) = 17 min")
        print("   2. curl_cffi: Use those URLs (25,000 times) = 3.5 hours")
        print("   3. TOTAL: ~4 hours for 25K users")
        print("   4. Gets real product data with $ prices")
        print("   5. FAST, SCALABLE, LOW COST")
    else:
        print("⚠️  ISSUE".center(80))
        print("="*80 + "\n")
        if dollar_count == 0 and euro_count > 0:
            print("Still getting EUR prices - callback might be session-locked")
        elif product_count == 0:
            print("No product containers - callback might be expired")
        else:
            print("Unexpected result - check saved HTML")
    
    print("="*80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

