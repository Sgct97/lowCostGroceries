"""
NUCLEAR OPTION: Every Anti-Detection Technique Combined

This combines:
1. Undetected ChromeDriver (UC)
2. Oxylabs ISP proxy (with proper extension-based auth)
3. Real browser profile with cookies
4. Human-like behavior (mouse movements, delays)
5. Different Google Shopping URLs
6. Realistic headers and fingerprints
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import zipfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Oxylabs credentials
PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"

def create_proxy_extension():
    """Create a Chrome extension for proxy authentication."""
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

    plugin_file = 'proxy_auth_plugin.zip'

    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_file


def test_all_urls():
    """Test multiple Google Shopping URLs with all anti-detection measures."""
    
    logger.info("\n" + "="*80)
    logger.info("🚀 NUCLEAR OPTION: ALL ANTI-DETECTION MEASURES COMBINED")
    logger.info("="*80)
    
    # URLs to try
    urls_to_test = [
        ("www.google.com standard", "https://www.google.com/search?tbm=shop&q=laptop&hl=en&gl=us"),
        ("www.google.com udm=28", "https://www.google.com/search?udm=28&q=laptop&hl=en&gl=us"),
        ("shopping.google.com", "https://shopping.google.com/search?q=laptop&hl=en&gl=us"),
        ("shopping.google.com m", "https://shopping.google.com/m/search?q=laptop"),
    ]
    
    # Create proxy extension
    logger.info("📦 Creating proxy authentication extension...")
    proxy_extension = create_proxy_extension()
    logger.info(f"✅ Proxy extension created: {proxy_extension}")
    
    # Setup Chrome options
    options = uc.ChromeOptions()
    
    # Load proxy extension
    options.add_extension(proxy_extension)
    
    # Anti-detection options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    options.add_argument(f'--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use a persistent user data dir (has cookies, history, etc)
    # options.add_argument(f'--user-data-dir=/tmp/chrome_profile_{int(time.time())}')
    
    logger.info("🚀 Launching undetected Chrome with Oxylabs proxy...")
    
    try:
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        
        logger.info("✅ Browser launched with proxy extension")
        logger.info(f"✅ Using proxy: {PROXY_HOST}:{PROXY_PORT}")
        
        results = {}
        
        for name, url in urls_to_test:
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing: {name}")
            logger.info(f"URL: {url}")
            logger.info('='*80)
            
            # Navigate
            driver.get(url)
            
            # Human-like behavior: wait and move mouse
            time.sleep(3)
            
            # Move mouse around
            try:
                actions = ActionChains(driver)
                actions.move_by_offset(100, 100).perform()
                time.sleep(0.5)
                actions.move_by_offset(50, 50).perform()
            except:
                pass
            
            # Wait for page to load
            time.sleep(3)
            
            # Get page content
            html = driver.page_source
            current_url = driver.current_url
            title = driver.title
            
            # Check status
            has_captcha = 'captcha' in html.lower() or 'recaptcha' in html.lower()
            has_challenge = 'unusual traffic' in html.lower() or 'automated' in html.lower()
            has_sorry = '/sorry/' in current_url
            has_products = ('liKJmf' in html or 'sh-dgr__' in html or 'KZmu8e' in html)
            has_shopping_content = '$' in html and ('price' in html.lower() or 'buy' in html.lower())
            
            # Log results
            logger.info(f"\n📊 Results for {name}:")
            logger.info(f"   Current URL: {current_url[:80]}...")
            logger.info(f"   Title: {title}")
            logger.info(f"   Page size: {len(html):,} bytes")
            logger.info(f"   ❌ CAPTCHA: {has_captcha}")
            logger.info(f"   ❌ Challenge: {has_challenge}")
            logger.info(f"   ❌ Sorry page: {has_sorry}")
            logger.info(f"   ✅ Products: {has_products}")
            logger.info(f"   ✅ Shopping content: {has_shopping_content}")
            
            success = not (has_captcha or has_challenge or has_sorry) and (has_products or has_shopping_content)
            
            results[name] = {
                'success': success,
                'has_captcha': has_captcha,
                'has_products': has_products,
                'url': current_url
            }
            
            if success:
                logger.info(f"\n🎉🎉🎉 SUCCESS WITH {name}!")
                
                # Save successful result
                with open(f"success_{name.replace(' ', '_')}.html", "w") as f:
                    f.write(html)
                
                driver.save_screenshot(f"success_{name.replace(' ', '_')}.png")
                
                logger.info(f"   Saved to: success_{name.replace(' ', '_')}.html/png")
                
                # Try to find callback URLs in network requests
                # (We'd need to use browsermob-proxy or similar for this)
                logger.info(f"   ⚠️  Now manually check DevTools Network tab for callback URLs!")
                
                # Keep browser open longer
                logger.info(f"\n⏳ Keeping browser open for 30 seconds - CHECK DEVTOOLS!")
                time.sleep(30)
                
                break  # Stop if we found a working URL
            else:
                # Save failed result for debugging
                with open(f"failed_{name.replace(' ', '_')}.html", "w") as f:
                    f.write(html)
                
                logger.info(f"   Saved failure to: failed_{name.replace(' ', '_')}.html")
                
                # Short delay before next URL
                time.sleep(2)
        
        # Final wait
        logger.info(f"\n⏳ Keeping browser open for 10 more seconds...")
        time.sleep(10)
        
        driver.quit()
        
        # Cleanup
        if os.path.exists(proxy_extension):
            os.remove(proxy_extension)
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Cleanup
        if os.path.exists(proxy_extension):
            os.remove(proxy_extension)
        
        return {}


if __name__ == "__main__":
    results = test_all_urls()
    
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    if not results:
        print("❌ Test crashed - see error above")
    else:
        success_count = sum(1 for r in results.values() if r['success'])
        
        print(f"\nTested {len(results)} URLs:")
        for name, result in results.items():
            status = "✅ SUCCESS" if result['success'] else "❌ BLOCKED"
            print(f"  {status} - {name}")
            if result['success']:
                print(f"           URL: {result['url']}")
        
        if success_count > 0:
            print(f"\n🎉 {success_count} URL(s) WORKED!")
            print("\nNEXT STEPS:")
            print("1. Check the success_*.html files")
            print("2. Open DevTools Network tab and look for /async/callback URLs")
            print("3. We can use that URL pattern for the TokenService")
        else:
            print("\n😤 All URLs blocked. Options:")
            print("1. Try with logged-in Google cookies (export from your browser)")
            print("2. Use CAPTCHA solving service (2captcha.com)")
            print("3. Manual callback capture for MVP")
    
    print("="*80)

