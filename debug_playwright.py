from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    Stealth().apply_stealth_sync(page)  # Apply stealth mode!
    
    requests_seen = []
    
    def log_request(request):
        url = request.url
        requests_seen.append(url)
        if 'shopping' in url or 'async' in url or 'callback' in url:
            print(f"REQUEST: {url[:120]}")
    
    page.on('request', log_request)
    
    print("Loading www.google.com with tbm=shop...")
    try:
        page.goto('https://www.google.com/search?q=milk&tbm=shop&udm=28', wait_until='networkidle', timeout=30000)
    except Exception as e:
        print(f"Error loading page: {e}")
    
    print("Scrolling...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    print("Waiting...")
    time.sleep(5)
    
    # Save screenshot
    page.screenshot(path='/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/page_screenshot.png')
    print("Screenshot saved")
    
    # Save HTML
    html = page.content()
    with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/page_content.html', 'w') as f:
        f.write(html)
    print(f"HTML saved ({len(html)} bytes)")
    
    print(f"\nTotal requests: {len(requests_seen)}")
    print("\nAll /async/ requests:")
    async_reqs = [req for req in requests_seen if '/async/' in req]
    for req in async_reqs:
        print(f"  {req[:150]}")
    
    if not async_reqs:
        print("  None found!")
        print("\nAll requests:")
        for req in requests_seen[:20]:
            print(f"  {req[:100]}")
    
    browser.close()

