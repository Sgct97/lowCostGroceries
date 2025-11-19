"""
Test Playwright + Stealth + Oxylabs ISP Proxy

This should bypass CAPTCHA since we're using:
1. Stealth mode (hides Playwright signatures)
2. ISP proxy (looks like a real residential user)
3. Realistic browser fingerprint
"""

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stealth = Stealth()

# Your Oxylabs credentials
PROXY = {
    "server": "http://isp.oxylabs.io:8001",
    "username": "lowCostGroceris_26SVt",
    "password": "AppleID_1234"
}

def test_with_proxy():
    """Test Google Shopping with stealth + Oxylabs proxy."""
    
    logger.info("\n" + "="*80)
    logger.info("TEST: Playwright + Stealth + Oxylabs ISP Proxy")
    logger.info("="*80)
    
    callback_found = None
    all_async_urls = []
    
    with sync_playwright() as p:
        # Launch with proxy
        browser = p.chromium.launch(
            headless=False,  # Show browser so you can see
            proxy=PROXY
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            permissions=["geolocation"]
        )
        
        page = context.new_page()
        
        # Apply stealth
        stealth.apply_stealth_sync(page)
        logger.info("✅ Stealth mode applied")
        logger.info(f"✅ Using proxy: {PROXY['server']}")
        
        # Listen for callback URLs
        def handle_response(response):
            nonlocal callback_found
            url = response.url
            
            if '/async/callback' in url:
                callback_found = url
                logger.info(f"🎉 FOUND CALLBACK: {url[:100]}")
            elif 'async' in url.lower() or 'shopping' in url.lower():
                all_async_urls.append(url)
        
        page.on("response", handle_response)
        
        # Navigate
        search_url = "https://www.google.com/search?udm=28&q=laptop&hl=en&gl=us"
        logger.info(f"\n🚀 Loading: {search_url}\n")
        
        page.goto(search_url, wait_until="networkidle", timeout=45000)
        
        # Wait and interact like a human
        logger.info("⏳ Waiting 5 seconds...")
        page.wait_for_timeout(5000)
        
        # Scroll
        logger.info("📜 Scrolling...")
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(2000)
        
        page.evaluate("window.scrollTo(0, 1000)")
        page.wait_for_timeout(2000)
        
        # Check page content
        html = page.content()
        
        # Save for inspection
        with open("proxy_test.html", "w") as f:
            f.write(html)
        
        page.screenshot(path="proxy_test.png")
        
        has_captcha = 'captcha' in html.lower() or 'recaptcha' in html.lower()
        has_challenge = 'challenge' in html.lower() or 'unusual traffic' in html.lower()
        has_products = 'liKJmf' in html or ('product' in html.lower() and '$' in html)
        
        logger.info("\n" + "="*80)
        logger.info("RESULTS")
        logger.info("="*80)
        logger.info(f"❌ CAPTCHA detected: {has_captcha}")
        logger.info(f"❌ Challenge page: {has_challenge}")
        logger.info(f"✅ Products found: {has_products}")
        logger.info(f"📊 Page size: {len(html):,} bytes")
        
        if callback_found:
            logger.info(f"\n🎉🎉🎉 SUCCESS! Found callback URL:")
            logger.info(f"   {callback_found[:150]}")
        else:
            logger.info(f"\n⚠️  No /async/callback found")
            
            if all_async_urls:
                logger.info(f"\n📋 Found {len(all_async_urls)} other async URLs:")
                for url in all_async_urls[:5]:
                    logger.info(f"   - {url[:120]}")
            else:
                logger.info(f"\n❌ No async URLs at all")
        
        if has_captcha or has_challenge:
            logger.info(f"\n😤 Still got blocked. Trying more aggressive evasion...")
        elif has_products:
            logger.info(f"\n✅ Got through! Products are visible!")
        
        logger.info(f"\n📸 Screenshot: proxy_test.png")
        logger.info(f"📄 HTML: proxy_test.html")
        
        # Keep browser open
        logger.info(f"\n⏳ Keeping browser open for 10 seconds...")
        page.wait_for_timeout(10000)
        
        browser.close()
    
    return callback_found, has_captcha, has_products

if __name__ == "__main__":
    callback, blocked, products = test_with_proxy()
    
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    if callback:
        print("✅✅✅ SUCCESS! We captured the callback URL!")
        print("     The hybrid architecture will work!")
    elif products and not blocked:
        print("✅ Got through CAPTCHA but no callback URL detected")
        print("   Google Shopping might not use callbacks for this region/query")
    elif blocked:
        print("❌ Still blocked by CAPTCHA")
        print("\n   Next steps to try:")
        print("   1. Use undetected-chromedriver instead of Playwright")
        print("   2. Add more human-like delays and mouse movements")
        print("   3. Use browser with logged-in Google cookies")
        print("   4. Try from different regions/proxies")
    else:
        print("⚠️  Unknown state - check the screenshots")
    
    print("="*80)

