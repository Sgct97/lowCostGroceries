"""
CRITICAL TEST: Can curl_cffi ALONE get products?

If YES: We can do 25K users with JUST curl_cffi!
- 25,000 × 0.5 sec = 3.5 hours total
- NO UC needed at all
- MAXIMUM scalability
"""

from curl_cffi import requests
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROXY = "http://lowCostGroceris_26SVt:AppleID_1234@isp.oxylabs.io:8001"

logger.info("\n" + "="*80)
logger.info("🚀 ULTIMATE TEST: curl_cffi ONLY (No UC)")
logger.info("="*80)
logger.info("\nIf this works, we can serve 25K users with JUST curl_cffi!\n")

# The URL that worked with UC
# Start with shopping.google.com homepage, then search
urls_to_test = [
    ("Direct search", "https://www.google.com/search?q=laptop&sca_esv=55588fd05011d482&udm=28&shopmd=1"),
    ("Shopping homepage search", "https://shopping.google.com/"),
]

for name, url in urls_to_test:
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing: {name}")
    logger.info(f"URL: {url[:80]}...")
    logger.info('='*80)
    
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
        
        # Save
        filename = f"curl_only_{name.replace(' ', '_')}.html"
        with open(filename, "w") as f:
            f.write(html)
        
        # Check
        has_captcha = 'captcha' in html.lower() or 'recaptcha' in html.lower()
        has_sorry = '/sorry/' in response.url or 'unusual traffic' in html.lower()
        
        # Look for products with regex (faster than BeautifulSoup)
        product_count = html.count('class="liKJmf"')
        
        # Extract some prices and titles
        prices = re.findall(r'class="lmQWe[^"]*"[^>]*>([^<]+)</span>', html)
        titles = re.findall(r'class="gkQHve[^"]*"[^>]*>([^<]+)</div>', html)
        
        logger.info(f"\n📊 Results:")
        logger.info(f"   CAPTCHA: {has_captcha} {'❌' if has_captcha else '✅'}")
        logger.info(f"   Sorry page: {has_sorry} {'❌' if has_sorry else '✅'}")
        logger.info(f"   Product containers: {product_count} {'✅' if product_count > 0 else '❌'}")
        logger.info(f"   Prices found: {len(prices)}")
        logger.info(f"   Titles found: {len(titles)}")
        
        if product_count > 0:
            logger.info(f"\n🎉🎉🎉 FOUND {product_count} PRODUCTS!")
            
            # Show a few
            for i, (title, price) in enumerate(zip(titles[:3], prices[:3]), 1):
                logger.info(f"\n   Product {i}:")
                logger.info(f"      Title: {title.strip()}")
                logger.info(f"      Price: {price.strip()}")
            
            logger.info(f"\n✅✅✅ curl_cffi ALONE WORKS!")
            logger.info(f"\n🚀 FOR 25K USERS:")
            logger.info(f"   - Method: curl_cffi + Oxylabs ONLY")
            logger.info(f"   - Speed: ~0.5 sec per user")
            logger.info(f"   - Total time: ~3.5 hours for 25K")
            logger.info(f"   - Cost: MINIMAL (just HTTP)")
            logger.info(f"   - NO UC needed!")
            logger.info(f"\n🎉 THIS IS THE SOLUTION!")
            
            # Success - no need to test other URLs
            break
            
        elif has_captcha or has_sorry:
            logger.warning(f"❌ Blocked by Google")
        else:
            logger.warning(f"⚠️  No products found (might need to wait for JS)")
        
        logger.info(f"\nSaved: {filename}\n")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

logger.info("\n" + "="*80)
logger.info("FINAL CONCLUSION")
logger.info("="*80)
logger.info("\nIf curl_cffi worked: PERFECT - use it for everything")
logger.info("If curl_cffi failed: Use UC to capture bgasy, then curl_cffi")
logger.info("="*80)

