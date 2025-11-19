import requests
from bs4 import BeautifulSoup
import json
import re

def get_shopping_results(query, location=None):
    """
    Full workflow: Load search page, extract params, then call async API
    """
    
    print("="*80)
    print(f"SCRAPING GOOGLE SHOPPING: '{query}'")
    print("="*80)
    
    # STEP 1: Load the initial shopping search page
    print("\nStep 1: Loading initial search page...")
    
    search_url = "https://www.google.com/search"
    params = {
        'q': query,
        'tbm': 'shop',  # Shopping mode
        'hl': 'en',
        'gl': 'us',
    }
    
    if location:
        params['near'] = location
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        session = requests.Session()
        response = session.get(search_url, params=params, headers=headers, timeout=15)
        
        print(f"✅ Status: {response.status_code}")
        print(f"Response size: {len(response.text):,} bytes")
        
        if response.status_code != 200:
            print("❌ Failed to load search page")
            return None
        
        # STEP 2: Extract products from HTML
        print("\nStep 2: Parsing products from HTML...")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Look for product data in HTML
        products_found = []
        
        # Try to find product containers
        # Google Shopping uses various class names
        product_selectors = [
            'div[data-docid]',
            'div.sh-dgr__content',
            'div[jsname]',
            'div[data-tds]',
        ]
        
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"  Found {len(elements)} elements with selector: {selector}")
        
        # Method 2: Look for JSON data embedded in scripts
        print("\nStep 3: Looking for embedded JSON data...")
        
        scripts = soup.find_all('script')
        for i, script in enumerate(scripts):
            if not script.string:
                continue
            
            content = str(script.string)
            
            # Look for arrays that might contain product data
            if 'price' in content.lower() and 'product' in content.lower():
                print(f"  Found script #{i} with product/price data ({len(content)} chars)")
                
                # Try to extract JSON-like structures
                # Google often embeds data as: var data = {...}; or window._data = {...};
                patterns = [
                    r'var\s+\w+\s*=\s*(\{.*?\});',
                    r'window\.\w+\s*=\s*(\{.*?\});',
                    r'\[(\{.*?"price".*?\})\]',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    if matches:
                        print(f"    Found {len(matches)} potential JSON objects")
                        
                        # Try to parse first match
                        for match in matches[:1]:
                            try:
                                # Extract just the JSON part
                                json_str = match
                                if json_str.startswith('{'):
                                    data = json.loads(json_str)
                                    print(f"    ✅ Parsed JSON successfully!")
                                    print(f"    Keys: {list(data.keys())[:10]}")
                                    
                                    # Save it
                                    with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/extracted_product_data.json', 'w') as f:
                                        json.dump(data, f, indent=2)
                                    print("    💾 Saved to: extracted_product_data.json")
                            except:
                                pass
        
        # Method 3: Extract any state/session data we need for async API
        print("\nStep 4: Extracting session parameters...")
        
        # Look for important parameters in the HTML
        params_found = {}
        
        # Extract 'ei' parameter (event ID)
        ei_match = re.search(r'[?&]ei=([^&"\']+)', response.text)
        if ei_match:
            params_found['ei'] = ei_match.group(1)
            print(f"  ✅ Found ei: {params_found['ei']}")
        
        # Extract 'ved' parameter
        ved_match = re.search(r'[?&]ved=([^&"\']+)', response.text)
        if ved_match:
            params_found['ved'] = ved_match.group(1)
            print(f"  ✅ Found ved: {params_found['ved'][:50]}...")
        
        # Extract 'sxsrf' (security token)
        sxsrf_match = re.search(r'sxsrf["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', response.text)
        if sxsrf_match:
            params_found['sxsrf'] = sxsrf_match.group(1)
            print(f"  ✅ Found sxsrf: {params_found['sxsrf'][:30]}...")
        
        # STEP 5: Now try the async endpoint with proper context
        print("\nStep 5: Calling async API with extracted params...")
        
        async_url = "https://www.google.com/async/bgasy"
        async_params = {
            'yv': '3',
            'cs': '0',
            'async': '_fmt:jspb',
            'shopmd': '1',
            'udm': '28',
            'q': query,  # Include the query
        }
        
        # Add extracted params
        if 'ei' in params_found:
            async_params['ei'] = params_found['ei']
        if 'ved' in params_found:
            async_params['ved'] = params_found['ved']
        
        async_headers = {
            'User-Agent': headers['User-Agent'],
            'Accept': '*/*',
            'Referer': response.url,  # Important: show where we came from
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        async_response = session.get(async_url, params=async_params, 
                                     headers=async_headers, timeout=10)
        
        print(f"  Status: {async_response.status_code}")
        print(f"  Size: {len(async_response.text):,} bytes")
        
        if async_response.status_code == 200:
            # Save async response
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/async_with_context.txt', 'w') as f:
                f.write(async_response.text)
            print("  💾 Saved async response")
            
            # Check for product data
            if any(term in async_response.text for term in ['price', 'product', 'merchant']):
                print("  ✅ Async response contains product data!")
        
        # STEP 6: Look for product data in original HTML using simpler patterns
        print("\nStep 6: Extracting products from HTML directly...")
        
        # Find all price elements
        prices = soup.find_all(string=re.compile(r'\$\d+'))
        print(f"  Found {len(prices)} price elements")
        
        # Find product containers around prices
        products = []
        for price_elem in prices[:10]:  # Check first 10
            # Find parent container
            parent = price_elem.find_parent(['div', 'a'])
            if parent:
                # Try to extract product info
                product = {
                    'price': price_elem.strip() if isinstance(price_elem, str) else price_elem.get_text().strip(),
                    'html': str(parent)[:200]
                }
                products.append(product)
        
        if products:
            print(f"  ✅ Extracted {len(products)} product containers")
            
            # Save products
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/extracted_products.json', 'w') as f:
                json.dump(products, f, indent=2)
            print("  💾 Saved to: extracted_products.json")
        
        # Save the full HTML for manual inspection
        with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/full_search_page.html', 'w') as f:
            f.write(response.text)
        print("\n💾 Saved full HTML to: full_search_page.html")
        
        return products
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                   FULL GOOGLE SHOPPING WORKFLOW TEST                     ║
    ║                   (Complete scraping process)                            ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Test with a query
    products = get_shopping_results("organic milk gallon", location="10001")
    
    print("\n" + "="*80)
    if products:
        print(f"✅ SUCCESS! Found {len(products)} products")
        print("\nSample product:")
        print(json.dumps(products[0], indent=2))
    else:
        print("⚠️  Need to analyze the saved HTML files")
        print("Check: full_search_page.html for the raw data")
    print("="*80)

