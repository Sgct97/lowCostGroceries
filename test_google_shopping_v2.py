import requests
from bs4 import BeautifulSoup
import json
import re

def test_google_shopping_search():
    """Test different Google Shopping URL patterns"""
    
    query = "milk"
    zip_code = "10001"  # NYC
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }
    
    # Try different URL patterns
    test_urls = [
        f"https://www.google.com/search?q={query}&tbm=shop",
        f"https://www.google.com/search?q={query}+near+{zip_code}&tbm=shop",
        f"https://www.google.com/search?q={query}&tbm=shop&tbs=local_avail:1,mr:1,sales:1",
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {url}")
        print('='*80)
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.text):,} characters")
            
            # Check for blocking indicators
            html_lower = response.text.lower()
            if 'captcha' in html_lower:
                print("⚠️  CAPTCHA detected")
                continue
            if 'unusual traffic' in html_lower:
                print("⚠️  Unusual traffic warning")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save first response for manual inspection
            if i == 1:
                with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/response_sample.txt', 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(response.text[:5000])  # First 5000 chars
                print("✓ Sample saved to response_sample.txt")
            
            # Look for various product indicators
            checks = {
                'div[data-docid]': soup.select('div[data-docid]'),
                'div[data-pck]': soup.select('div[data-pck]'),
                'div[data-tds]': soup.select('div[data-tds]'),
                'span containing $': soup.find_all('span', string=re.compile(r'\$\d+')),
                'divs with "sh-" class': soup.find_all('div', class_=re.compile(r'sh-')),
            }
            
            print("\n📊 Element Counts:")
            for desc, elements in checks.items():
                print(f"  {desc}: {len(elements)}")
                if elements and len(elements) > 0:
                    print(f"    Sample: {str(elements[0])[:200]}")
            
            # Look for script tags with data
            scripts = soup.find_all('script')
            json_scripts = [s for s in scripts if s.string and ('{' in str(s.string) or '[' in str(s.string))]
            print(f"\n  Scripts with potential JSON: {len(json_scripts)}")
            
            # Check if it's a redirect or error page
            title = soup.find('title')
            if title:
                print(f"\n📄 Page Title: {title.string}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_specific_product():
    """Test with a specific product search that should definitely return results"""
    
    print(f"\n{'='*80}")
    print("Testing with specific grocery product")
    print('='*80)
    
    # More specific search
    url = "https://www.google.com/search?q=organic+milk+gallon&tbm=shop"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        # Look for price patterns in raw HTML
        prices = re.findall(r'\$\d+\.\d{2}', response.text)
        print(f"Found {len(set(prices))} unique prices: {list(set(prices))[:10]}")
        
        # Look for merchant names
        common_stores = ['walmart', 'target', 'whole foods', 'kroger', 'safeway', 'costco']
        found_stores = [store for store in common_stores if store in response.text.lower()]
        print(f"Found stores: {found_stores}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Google Shopping Scraping Test - v2")
    print("Testing if we can extract product data without browser automation\n")
    
    test_google_shopping_search()
    test_specific_product()
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("Check response_sample.txt to see actual HTML structure")
    print("If no products found, Google may be returning JavaScript-rendered content")
    print("="*80)

