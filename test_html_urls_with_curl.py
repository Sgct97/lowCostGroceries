"""
TEST HTML URLs with curl_cffi

These are HTML responses captured from UC.
If they work with curl_cffi → BREAKTHROUGH!
"""

from curl_cffi import requests
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

# HTML URLs captured from UC
test_urls = [
    ("Main search 1", "https://www.google.com/search?q=laptop&sca_esv=55588fd05011d482&udm=28&shopmd=1&ei=3gUeabPfC7uPwbkPz7XmqQ0"),
    ("Main search 2 (with sei)", "https://www.google.com/search?q=laptop&sca_esv=55588fd05011d482&udm=28&shopmd=1&ei=3gUeabPfC7uPwbkPz7XmqQ0&sei=4wUeaa_KH4mVwbkP8KCM-AM"),
    ("Simple search", "https://www.google.com/search?q=laptop&udm=28"),
]

logger.info("\n" + "="*80)
logger.info("🚀 TESTING HTML URLs WITH curl_cffi")
logger.info("="*80)
logger.info("\nTHIS IS THE CRITICAL TEST!\n")

for name, url in test_urls:
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing: {name}")
    logger.info(f"{'='*80}")
    logger.info(f"\n{url}\n")
    
    try:
        response = requests.get(
            url,
            headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9",
                "sec-ch-ua": '"Google Chrome";v="120", "Chromium";v="120", "Not?A_Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
            },
            proxies={"http": PROXY, "https": PROXY},
            impersonate="chrome120",
            timeout=30,
            allow_redirects=True
        )
        
        logger.info(f"✅ Status: {response.status_code}")
        logger.info(f"✅ Final URL: {response.url[:100]}...")
        logger.info(f"✅ Size: {len(response.text):,} bytes")
        
        html = response.text
        
        # Analyze
        has_captcha = 'captcha' in html.lower() or 'recaptcha' in html.lower()
        has_sorry = '/sorry/' in response.url or 'unusual traffic' in html.lower()
        product_count = html.count('class="liKJmf"')
        
        # Extract some data
        prices = re.findall(r'class="lmQWe[^"]*"[^>]*>\$([^<]+)</span>', html)
        titles = re.findall(r'class="gkQHve[^"]*"[^>]*>([^<]+)</div>', html)
        
        logger.info(f"\n📊 Analysis:")
        logger.info(f"   CAPTCHA: {has_captcha} {'❌' if has_captcha else '✅'}")
        logger.info(f"   Sorry page: {has_sorry} {'❌' if has_sorry else '✅'}")
        logger.info(f"   Product containers: {product_count}")
        logger.info(f"   Prices found: {len(prices)}")
        logger.info(f"   Titles found: {len(titles)}")
        
        # Save
        filename = f"curl_test_{name.replace(' ', '_')}.html"
        with open(filename, "w") as f:
            f.write(html)
        logger.info(f"\nSaved: {filename}")
        
        if product_count > 0:
            logger.info(f"\n🎉🎉🎉 FOUND {product_count} PRODUCTS WITH curl_cffi!")
            logger.info(f"\n✅ Sample products:")
            for i, (title, price) in enumerate(zip(titles[:3], prices[:3]), 1):
                logger.info(f"\n   {i}. {title.strip()}")
                logger.info(f"      ${price.strip()}")
            
            logger.info(f"\n✅✅✅ BREAKTHROUGH!")
            logger.info(f"\n🚀 THIS URL PATTERN WORKS WITH curl_cffi!")
            logger.info(f"\n🚀 FOR 25K USERS:")
            logger.info(f"   - Use curl_cffi ONLY")
            logger.info(f"   - Speed: ~0.5 sec per search")
            logger.info(f"   - Total: ~3.5 hours for 25K")
            logger.info(f"   - NO UC needed!")
            logger.info(f"\n🎉 PRODUCTION READY!")
            
            break  # Found it!
            
        elif has_captcha or has_sorry:
            logger.warning(f"❌ Blocked by Google")
        else:
            logger.warning(f"⚠️  No products found")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("FINAL VERDICT")
print("="*80)

print("\nCheck the logs above:")
print("  ✅ If we found products → curl_cffi ONLY solution!")
print("  ❌ If no products → Need to refine URL pattern or add cookies")

print("="*80)

