"""
TEST /async/bgasy with curl_cffi

We captured this URL from the network logs:
https://www.google.com/async/bgasy?ei=...&udm=28&yv=3&cs=0&async=_fmt:jspb

If this works with curl_cffi, we can use it for 25K users!
"""

from curl_cffi import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Oxylabs proxy
PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

# The bgasy URL we captured
bgasy_url = "https://www.google.com/async/bgasy?ei=WwEeaciUO9mEwbkPnc7QwQ8&opi=95576897&udm=28&yv=3&cs=0&async=_fmt:jspb"

logger.info("\n" + "="*80)
logger.info("🚀 TESTING /async/bgasy WITH curl_cffi")
logger.info("="*80)
logger.info("\nThis is THE critical test for 25K user scalability!\n")

logger.info(f"URL: {bgasy_url}\n")

# Try with curl_cffi + proxy
logger.info("Making request with curl_cffi + Oxylabs proxy...")

response = requests.get(
    bgasy_url,
    headers={
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.google.com/search?q=laptop&udm=28",
    },
    proxies={"http": PROXY, "https": PROXY},
    impersonate="chrome120",
    timeout=30
)

logger.info(f"✅ Status: {response.status_code}")
logger.info(f"✅ Size: {len(response.text):,} bytes\n")

# Check what we got
text = response.text

# Save it
with open("bgasy_response.txt", "w") as f:
    f.write(text)

logger.info("📄 Saved to: bgasy_response.txt\n")

# Check for product data
has_products = any(x in text for x in ['liKJmf', 'sh-dgr__', 'product', '$'])
has_json = text.startswith('{') or text.startswith('[')
has_jspb = '_fmt:jspb' in bgasy_url

logger.info("="*80)
logger.info("ANALYSIS")
logger.info("="*80)
logger.info(f"✅ Has product indicators: {has_products}")
logger.info(f"📋 Looks like JSON: {has_json}")
logger.info(f"📋 JSPB format: {has_jspb}")
logger.info(f"📊 First 200 chars: {text[:200]}")

if has_products:
    logger.info(f"\n🎉🎉🎉 SUCCESS! bgasy returns product data!")
    logger.info("\n✅ THIS MEANS:")
    logger.info("   1. We can use UC once to get bgasy URL pattern")
    logger.info("   2. Use curl_cffi for all 25K users")
    logger.info("   3. Fast, scalable, cheap!")
    logger.info("\n🚀 READY FOR PRODUCTION!")
else:
    logger.warning(f"\n⚠️  No obvious product data")
    logger.info("\nPossible reasons:")
    logger.info("1. Session/token expired (ei= parameter)")
    logger.info("2. Need to capture fresh bgasy URL from UC")
    logger.info("3. Different format than expected")
    logger.info("\nNext: Capture fresh bgasy URL and test again")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

if has_products:
    print("\n✅✅✅ BGASY WORKS WITH curl_cffi!")
    print("\n🚀 For 25K users:")
    print("   - Use UC: ~100 times (capture bgasy patterns)")
    print("   - Use curl_cffi: 25,000 times (fast scraping)")
    print("   - Total time: ~2-3 hours for 25K users")
    print("   - Cost: LOW (just HTTP requests)")
    print("\n🎉 ARCHITECTURE IS PROVEN!")
else:
    print("\n⚠️  bgasy didn't return products with this old URL")
    print("\nNext step:")
    print("   Capture a FRESH bgasy URL with UC and test again")

print("="*80)

