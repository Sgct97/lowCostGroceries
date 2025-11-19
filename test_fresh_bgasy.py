"""
TEST FRESH BGASY URLs with curl_cffi

These are JUST captured from UC with scrolling.
If they work → HYBRID ARCHITECTURE IS PROVEN!
"""

from curl_cffi import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

# Fresh bgasy URLs just captured
bgasy_urls = [
    "https://www.google.com/async/bgasy?ei=7gQeae3AH7aNwbkPvIWH2Aw&opi=95576897&udm=28&yv=3&cs=0&async=_fmt:jspb",
    "https://www.google.com/async/bgasy?ei=9gQeafevOb-wkvQPuOHJiQc&opi=95576897&sca_esv=55588fd05011d482&shopmd=1&udm=28&yv=3&cs=0&async=_fmt:jspb",
]

logger.info("\n" + "="*80)
logger.info("🚀 TESTING FRESH BGASY URLs WITH curl_cffi")
logger.info("="*80)
logger.info("\nTHIS IS THE CRITICAL TEST FOR 25K USER SCALABILITY!\n")

for i, url in enumerate(bgasy_urls, 1):
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing bgasy URL #{i}")
    logger.info(f"{'='*80}")
    logger.info(f"\n{url}\n")
    
    try:
        response = requests.get(
            url,
            headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "referer": "https://www.google.com/search?q=laptop&udm=28",
                "sec-ch-ua": '"Google Chrome";v="120", "Chromium";v="120", "Not?A_Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            },
            proxies={"http": PROXY, "https": PROXY},
            impersonate="chrome120",
            timeout=30
        )
        
        logger.info(f"✅ Status: {response.status_code}")
        logger.info(f"✅ Size: {len(response.text):,} bytes")
        
        text = response.text
        
        # Save
        filename = f"bgasy_test_{i}.txt"
        with open(filename, "w") as f:
            f.write(text)
        
        # Analyze
        has_products = 'liKJmf' in text or 'product' in text.lower()
        has_prices = '$' in text or 'price' in text.lower()
        is_json = text.strip().startswith(('{', '[', ")]}"))  # XSSI-protected JSON
        
        logger.info(f"\n📊 Analysis:")
        logger.info(f"   Product indicators: {has_products}")
        logger.info(f"   Price indicators: {has_prices}")
        logger.info(f"   JSON format: {is_json}")
        logger.info(f"   First 200 chars: {text[:200]}")
        
        if has_products or has_prices:
            logger.info(f"\n🎉🎉🎉 URL #{i} HAS PRODUCT DATA!")
        else:
            logger.warning(f"\n⚠️  URL #{i} doesn't seem to have product data")
        
        logger.info(f"\nSaved: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Error testing URL #{i}: {e}")

print("\n" + "="*80)
print("FINAL VERDICT")
print("="*80)

print("\nIf any bgasy URL returned product data:")
print("  ✅ HYBRID ARCHITECTURE WORKS!")
print("  🚀 For 25K users:")
print("     1. UC: Capture bgasy patterns (~100 times)")
print("     2. curl_cffi: Use bgasy URLs (25,000 times)")
print("     3. Speed: ~0.5 sec per curl_cffi call")
print("     4. Total: ~4 hours for 25K users")
print("\nIf bgasy URLs expired:")
print("  📋 Pattern identified: /async/bgasy?ei=XXX&opi=XXX&udm=28&yv=3")
print("  ⚠️  May need cookies or fresher capture")
print("  🔄 Fallback: Parse products from UC HTML directly")

print("="*80)

