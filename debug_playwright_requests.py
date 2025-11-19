"""
Debug Playwright Network Requests

This script will show us ALL network requests made when loading Google Shopping,
so we can see if callback URLs are being triggered and what pattern they use.
"""

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
stealth = Stealth()

def debug_google_shopping():
    """Load Google Shopping and log all network requests."""
    
    all_requests = []
    all_responses = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        
        page = context.new_page()
        
        # Apply stealth mode
        stealth.apply_stealth_sync(page)
        logger.info("✅ Stealth mode applied")
        
        # Log ALL requests
        def log_request(request):
            all_requests.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type
            })
            
            # Log interesting patterns
            if any(pattern in request.url.lower() for pattern in ['async', 'callback', 'shopping', 'gen_204']):
                logger.info(f"🔵 REQUEST: {request.method} {request.url[:120]}")
        
        # Log ALL responses
        def log_response(response):
            all_responses.append({
                'url': response.url,
                'status': response.status,
                'content_type': response.headers.get('content-type', 'unknown')
            })
            
            # Highlight callback URLs
            if '/async/callback' in response.url:
                logger.info(f"🟢 CALLBACK RESPONSE: {response.url[:120]}")
            elif 'async' in response.url.lower():
                logger.info(f"🟡 ASYNC RESPONSE: {response.url[:120]}")
        
        page.on("request", log_request)
        page.on("response", log_response)
        
        # Navigate
        search_url = "https://www.google.com/search?udm=28&q=laptop&hl=en&gl=us"
        logger.info(f"\n🚀 Loading: {search_url}\n")
        
        page.goto(search_url, wait_until="networkidle", timeout=30000)
        
        # Wait and scroll to trigger lazy content
        logger.info("\n⏳ Waiting 3 seconds...")
        page.wait_for_timeout(3000)
        
        logger.info("📜 Scrolling down...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        page.wait_for_timeout(2000)
        
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        # Save screenshot and HTML
        page.screenshot(path="debug_screenshot.png")
        with open("debug_page.html", "w") as f:
            f.write(page.content())
        
        logger.info(f"\n📸 Screenshot saved: debug_screenshot.png")
        logger.info(f"📄 HTML saved: debug_page.html")
        
        # Summary
        logger.info(f"\n" + "="*80)
        logger.info(f"NETWORK REQUEST SUMMARY")
        logger.info(f"="*80)
        logger.info(f"Total requests: {len(all_requests)}")
        logger.info(f"Total responses: {len(all_responses)}")
        
        # Find callback patterns
        callback_reqs = [r for r in all_requests if 'callback' in r['url'].lower()]
        async_reqs = [r for r in all_requests if 'async' in r['url'].lower()]
        
        logger.info(f"\n🔍 Callback requests: {len(callback_reqs)}")
        for req in callback_reqs:
            logger.info(f"   {req['url'][:150]}")
        
        logger.info(f"\n🔍 Async requests: {len(async_reqs)}")
        for req in async_reqs[:10]:  # First 10
            logger.info(f"   {req['url'][:150]}")
        
        # Check page content
        html = page.content()
        has_products = 'liKJmf' in html or 'product' in html.lower()
        logger.info(f"\n🛍️  Page has products: {has_products}")
        
        # Keep browser open for 5 seconds
        logger.info(f"\n⏳ Keeping browser open for 5 seconds so you can see it...")
        page.wait_for_timeout(5000)
        
        browser.close()
        
        return callback_reqs, async_reqs

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DEBUG: Google Shopping Network Requests")
    print("="*80)
    print("\nThis will open a browser and log all network requests.")
    print("Look for /async/callback or similar patterns.\n")
    
    callback_reqs, async_reqs = debug_google_shopping()
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    if callback_reqs:
        print(f"\n✅ Found {len(callback_reqs)} callback request(s)!")
        print("\nOur TokenService should be able to capture these.")
    elif async_reqs:
        print(f"\n⚠️  No /async/callback, but found {len(async_reqs)} other async requests")
        print("\nGoogle Shopping might be using a different pattern.")
        print("Top async URLs:")
        for req in async_reqs[:5]:
            print(f"  - {req['url'][:120]}")
    else:
        print("\n❌ No callback or async requests found!")
        print("\nGoogle Shopping might be:")
        print("  1. Rendering all data in initial HTML (server-side)")
        print("  2. Using a different async pattern we're not detecting")
        print("  3. Blocking our headless browser")
    
    print("\n📸 Check debug_screenshot.png to see what Google showed us")
    print("📄 Check debug_page.html for the page content")
    print("="*80)

