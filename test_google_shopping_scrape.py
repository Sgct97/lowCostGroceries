import requests
from bs4 import BeautifulSoup
import json
import re

def test_direct_request():
    """Test direct HTTP request to Google Shopping"""
    
    # Example: Search for "milk" in grocery category near a ZIP
    query = "milk grocery"
    zip_code = "90210"  # Beverly Hills for testing
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Try Google Shopping URL pattern
    url = f"https://www.google.com/search?q={query}&tbm=shop&near={zip_code}"
    
    print(f"Testing URL: {url}")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)} characters")
        print("=" * 80)
        
        if response.status_code == 200:
            # Save HTML for inspection
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/google_shopping_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("✓ HTML saved to google_shopping_response.html")
            
            # Try to parse some basic info
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for product cards/divs
            print("\n--- Looking for product data ---")
            
            # Common Google Shopping selectors
            products = soup.find_all('div', {'class': re.compile(r'sh-dgr__content|product')})
            print(f"Found {len(products)} potential product containers")
            
            # Look for prices
            prices = soup.find_all('span', {'class': re.compile(r'price|amount')})
            print(f"Found {len(prices)} potential price elements")
            
            # Look for product titles
            titles = soup.find_all(['h3', 'h4', 'span'], {'class': re.compile(r'title|name')})
            print(f"Found {len(titles)} potential title elements")
            
            # Check for JSON-LD structured data
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            print(f"Found {len(scripts)} JSON-LD scripts")
            
            if scripts:
                print("\n--- JSON-LD Data Found ---")
                for i, script in enumerate(scripts[:2]):  # Print first 2
                    try:
                        data = json.loads(script.string)
                        print(f"\nScript {i+1}:")
                        print(json.dumps(data, indent=2)[:500])  # First 500 chars
                    except:
                        pass
            
            # Look for any data-* attributes that might contain JSON
            elements_with_data = soup.find_all(attrs={'data-docid': True})
            print(f"\nFound {len(elements_with_data)} elements with data-docid")
            
            # Check if we're blocked or redirected
            if 'captcha' in response.text.lower():
                print("\n⚠️  CAPTCHA detected - Google is blocking")
                return False
            
            if 'sorry' in response.url.lower():
                print("\n⚠️  Redirected to sorry page - blocked")
                return False
                
            print("\n✓ Request successful, no obvious blocking")
            return True
            
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_google_shopping_api_pattern():
    """Test if there's an API-like endpoint similar to Google Maps"""
    
    print("\n" + "=" * 80)
    print("Testing API-style endpoints...")
    print("=" * 80)
    
    # Try patterns similar to Google Maps APIs
    test_urls = [
        "https://www.google.com/shopping/product/",
        "https://shopping.google.com/",
        "https://serpapi.com/search"  # Just to show the pattern, not actually calling
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    
    for url in test_urls[:2]:  # Skip serpapi
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"\n{url}")
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        except Exception as e:
            print(f"\n{url}")
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Testing Google Shopping Scraping without Browser Automation")
    print("=" * 80)
    
    success = test_direct_request()
    test_google_shopping_api_pattern()
    
    print("\n" + "=" * 80)
    if success:
        print("✓ Basic scraping appears feasible")
        print("Check google_shopping_response.html to see actual structure")
    else:
        print("⚠️  Direct scraping may be blocked/limited")
        print("May need browser automation or proxies")

