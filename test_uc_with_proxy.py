"""
Test Undetected ChromeDriver + Oxylabs

undetected-chromedriver is SPECIFICALLY designed to bypass Google's bot detection.
It patches Chrome to remove all automation signatures.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Oxylabs proxy
PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"

def test_uc():
    """Test with undetected-chromedriver."""
    
    logger.info("\n" + "="*80)
    logger.info("TEST: Undetected ChromeDriver + Oxylabs ISP Proxy")
    logger.info("="*80)
    logger.info("\nThis is the MOST POWERFUL anti-detection tool.")
    logger.info("If this doesn't work, we'll need to try cookies or CAPTCHA solving.\n")
    
    # Setup Chrome options
    options = uc.ChromeOptions()
    
    # Add proxy with authentication
    # NOTE: Proxy auth requires a Chrome extension with UC, testing WITHOUT proxy first
    # proxy_string = f"{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    # options.add_argument(f'--proxy-server=http://{PROXY_HOST}:{PROXY_PORT}')
    
    # Additional stealth options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument(f'--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # For debugging - show browser
    # options.add_argument('--headless=new')  # Comment out to see browser
    
    logger.info("🚀 Launching undetected Chrome...")
    
    try:
        # Create driver (let UC auto-detect Chrome version)
        driver = uc.Chrome(options=options, use_subprocess=True)
        
        logger.info("✅ Browser launched")
        logger.info(f"⚠️  Testing WITHOUT proxy first (proxy auth needs extension)")
        
        # Track network requests (this is harder with Selenium, but we can check page content)
        callback_found = False
        
        # Navigate
        search_url = "https://www.google.com/search?udm=28&q=laptop&hl=en&gl=us"
        logger.info(f"\n🚀 Loading: {search_url}\n")
        
        driver.get(search_url)
        
        # Wait for page to load
        logger.info("⏳ Waiting for page to load...")
        time.sleep(5)
        
        # Get page source
        html = driver.page_source
        
        # Check what we got
        has_captcha = 'captcha' in html.lower() or 'recaptcha' in html.lower()
        has_challenge = 'unusual traffic' in html.lower() or 'automated requests' in html.lower()
        has_products = 'shopping' in html.lower() and '$' in html
        has_product_class = 'liKJmf' in html or 'sh-dgr__' in html
        
        # Save for inspection
        with open("uc_test.html", "w") as f:
            f.write(html)
        
        driver.save_screenshot("uc_test.png")
        
        logger.info("\n" + "="*80)
        logger.info("RESULTS")
        logger.info("="*80)
        logger.info(f"❌ CAPTCHA detected: {has_captcha}")
        logger.info(f"❌ Challenge page: {has_challenge}")
        logger.info(f"✅ Products/shopping content: {has_products}")
        logger.info(f"✅ Product containers: {has_product_class}")
        logger.info(f"📊 Page size: {len(html):,} bytes")
        
        # Try to find product elements
        try:
            # Wait for products to appear
            wait = WebDriverWait(driver, 10)
            
            # Common Google Shopping selectors
            selectors_to_try = [
                "div.sh-dgr__content",
                "div.liKJmf",
                "div[data-sh-product-id]",
                "div.KZmu8e",
                "a.shntl"
            ]
            
            found_elements = []
            for selector in selectors_to_try:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        found_elements.append((selector, len(elements)))
                        logger.info(f"✅ Found {len(elements)} elements with selector: {selector}")
                except:
                    pass
            
            if not found_elements:
                logger.info("❌ No product elements found with any selector")
        
        except Exception as e:
            logger.info(f"⚠️  Could not check for elements: {e}")
        
        # Scroll and wait like a human
        logger.info("\n📜 Scrolling like a human...")
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        
        # Check page title
        logger.info(f"\n📄 Page title: {driver.title}")
        logger.info(f"📄 Current URL: {driver.current_url}")
        
        logger.info(f"\n📸 Screenshot: uc_test.png")
        logger.info(f"📄 HTML: uc_test.html")
        
        # Keep browser open so you can see
        logger.info(f"\n⏳ Keeping browser open for 10 seconds...")
        logger.info(f"   You should see the actual Google page now!")
        time.sleep(10)
        
        # Close
        driver.quit()
        
        return not has_captcha and (has_products or has_product_class), has_captcha
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, True

if __name__ == "__main__":
    success, blocked = test_uc()
    
    print("\n" + "="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    if success:
        print("🎉🎉🎉 SUCCESS! Undetected ChromeDriver bypassed the CAPTCHA!")
        print("\n✅ We can use this for the TokenService!")
        print("✅ Now we need to capture the callback URLs from network requests.")
        print("\nNext step: Add network request interception to capture callbacks.")
    elif blocked:
        print("😤 Still blocked even with undetected-chromedriver.")
        print("\nOptions:")
        print("1. Try with authenticated Google cookies")
        print("2. Use CAPTCHA solving service (2captcha, anticaptcha)")
        print("3. Accept that we need manual intervention for initial session")
        print("4. Check if proxy is working (might not be authenticating)")
    else:
        print("⚠️  Unclear result - check the screenshots and HTML")
    
    print("="*80)

