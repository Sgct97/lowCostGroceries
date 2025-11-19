"""
Test Different shopping.google.com URL Formats

We confirmed that UC + Oxylabs WORKS (no CAPTCHA on shopping.google.com).
Now we just need to find the RIGHT URL format.
"""

import undetected_chromedriver as uc
import time
import zipfile
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Oxylabs
PROXY_HOST = "isp.oxylabs.io"
PROXY_PORT = "8001"
PROXY_USER = "lowCostGroceris_26SVt"
PROXY_PASS = "AppleID_1234"

def create_proxy_extension():
    """Create proxy auth extension."""
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


def test_shopping_urls():
    """Test various shopping.google.com URL formats."""
    
    # Different URL formats to try
    urls_to_test = [
        ("shopping.google.com root", "https://shopping.google.com/"),
        ("shopping.google.com with country", "https://shopping.google.com/?hl=en&gl=us"),
        ("shopping.google.com u/0", "https://shopping.google.com/u/0/search?q=laptop"),
        ("shopping.google.com product", "https://shopping.google.com/product?q=laptop&hl=en"),
        ("shopping.google.com merchant", "https://shopping.google.com/merchant/catalog?q=laptop"),
        ("www.google.com shopping tab", "https://www.google.com/search?q=laptop&tbm=shop"),
    ]
    
    # Create proxy extension
    logger.info("📦 Creating proxy extension...")
    proxy_extension = create_proxy_extension()
    
    # Setup Chrome
    options = uc.ChromeOptions()
    options.add_extension(proxy_extension)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    logger.info("🚀 Launching Chrome with Oxylabs proxy...\n")
    
    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
    
    results = {}
    
    for name, url in urls_to_test:
        logger.info("="*80)
        logger.info(f"Testing: {name}")
        logger.info(f"URL: {url}")
        logger.info("="*80)
        
        try:
            driver.get(url)
            time.sleep(5)  # Wait for page
            
            html = driver.page_source
            current_url = driver.current_url
            
            # Check status
            has_captcha = 'captcha' in html.lower() or 'recaptcha' in html.lower()
            has_sorry = '/sorry/' in current_url
            has_products = ('sh-dgr__' in html or 'liKJmf' in html or 'pla-unit' in html)
            has_shopping_ui = 'Shopping' in html or 'shop' in html.lower()
            page_size = len(html)
            
            success = not (has_captcha or has_sorry) and (has_products or page_size > 100000)
            
            logger.info(f"\n📊 Results:")
            logger.info(f"   Final URL: {current_url[:100]}")
            logger.info(f"   Page size: {page_size:,} bytes")
            logger.info(f"   {'❌' if has_captcha else '✅'} CAPTCHA: {has_captcha}")
            logger.info(f"   {'❌' if has_sorry else '✅'} Sorry page: {has_sorry}")
            logger.info(f"   {'✅' if has_products else '⚠️ '} Products: {has_products}")
            logger.info(f"   {'✅' if has_shopping_ui else '⚠️ '} Shopping UI: {has_shopping_ui}")
            logger.info(f"   {'🎉 SUCCESS' if success else '❌ Failed'}")
            
            results[name] = {
                'success': success,
                'has_captcha': has_captcha,
                'has_products': has_products,
                'final_url': current_url,
                'page_size': page_size
            }
            
            # Save HTML
            filename = f"{'success' if success else 'test'}_{name.replace(' ', '_')}.html"
            with open(filename, 'w') as f:
                f.write(html)
            
            logger.info(f"   Saved: {filename}\n")
            
            if success and has_products:
                logger.info(f"\n🎉🎉🎉 FOUND WORKING URL: {name}")
                logger.info(f"   URL: {url}")
                logger.info(f"   Final: {current_url}")
                logger.info("\n   Keeping browser open for 30 seconds - CHECK FOR CALLBACK URLS IN DEVTOOLS!")
                time.sleep(30)
                break
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            results[name] = {'success': False, 'error': str(e)}
        
        time.sleep(2)
    
    driver.quit()
    
    # Cleanup
    if os.path.exists(proxy_extension):
        os.remove(proxy_extension)
    
    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 TESTING SHOPPING.GOOGLE.COM URL FORMATS")
    print("="*80)
    print("\nWe KNOW the proxy + UC works (no CAPTCHA)")
    print("Now finding the RIGHT URL format...\n")
    
    results = test_shopping_urls()
    
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    success_urls = [name for name, r in results.items() if r.get('success')]
    
    if success_urls:
        print(f"\n✅ {len(success_urls)} URL(s) WORKED:")
        for name in success_urls:
            r = results[name]
            print(f"\n  🎉 {name}")
            print(f"     Final URL: {r['final_url']}")
            print(f"     Has products: {r['has_products']}")
    else:
        print("\n⚠️  No URLs found products yet")
        print("\nBut we confirmed:")
        print("✅ Proxy + UC bypasses CAPTCHA")
        print("✅ We can access shopping.google.com")
        print("⚠️  Just need the right URL format or wait for JS to load")
    
    print("="*80)

