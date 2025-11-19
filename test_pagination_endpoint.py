import requests
from bs4 import BeautifulSoup
import json
import re

def test_pagination_endpoint():
    """Test the potential pagination/more results endpoint"""
    
    print("="*80)
    print("TESTING PAGINATION ENDPOINT")
    print("="*80)
    
    # Base URL
    base_url = "https://www.google.com/search"
    
    # Key parameters extracted from your URL
    params = {
        'q': 'milk',
        'tbm': 'shop',
        'start': '30',  # Pagination offset
        'sa': 'N',
        'async': 'arc_id:srp_test,ffilt:all,ve_name:MoreResultsContainer,_fmt:pc'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.google.com/search?q=milk&tbm=shop',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    print(f"\nURL: {base_url}")
    print(f"Params: {params}")
    print("\n" + "="*80)
    
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        
        print(f"✅ Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response size: {len(response.text):,} bytes")
        
        # Save response
        with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/pagination_response.html', 'w') as f:
            f.write(response.text)
        print("💾 Saved to: pagination_response.html")
        
        # Check if it starts with XSSI protection
        content = response.text
        if content.startswith(')]}\''):
            print("\n✅ Found XSSI protection prefix - this is an API response!")
            content = content[4:]
            
            # Try to parse as JSON
            try:
                data = json.loads(content)
                print("\n🎉 SUCCESS! It's JSON!")
                print(f"Type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"Array length: {len(data)}")
                
                # Save JSON
                with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/pagination_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("💾 Saved JSON to: pagination_data.json")
                
            except json.JSONDecodeError:
                print("Not standard JSON format")
        
        # Look for product data patterns
        print("\n" + "="*80)
        print("Looking for product data patterns...")
        print("="*80)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for product cards
        product_indicators = {
            'Price elements': len(soup.find_all(string=re.compile(r'\$\d+'))),
            'Product divs': len(soup.find_all('div', class_=re.compile(r'product|item|card', re.I))),
            'Images': len(soup.find_all('img')),
            'Links': len(soup.find_all('a')),
        }
        
        print("\nElement counts:")
        for key, count in product_indicators.items():
            print(f"  {key}: {count}")
            if count > 0:
                print(f"    ✅ Found {count} elements!")
        
        # Check raw text for product terms
        sample = response.text[:2000].lower()
        keywords = ['price', 'product', 'merchant', 'title', 'store', 'buy']
        found = [k for k in keywords if k in sample]
        
        if found:
            print(f"\n✅ Found keywords in response: {found}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simplified_async():
    """Test with minimal async parameters"""
    
    print("\n" + "="*80)
    print("TESTING SIMPLIFIED ASYNC REQUEST")
    print("="*80)
    
    url = "https://www.google.com/search"
    
    params = {
        'q': 'milk',
        'tbm': 'shop',
        'start': '10',
        'async': '_fmt:json'  # Try requesting JSON format
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, */*',
        'Referer': 'https://www.google.com/search?q=milk&tbm=shop',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Size: {len(response.text):,} bytes")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        # Check if it's JSON
        if 'json' in response.headers.get('Content-Type', '').lower():
            print("✅ JSON response!")
            try:
                data = response.json()
                print(f"Data type: {type(data)}")
                with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/async_json.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("💾 Saved to: async_json.json")
            except:
                pass
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║           TESTING THE PAGINATION/MORE RESULTS ENDPOINT                   ║
    ║           (You might have found it!)                                     ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    success = test_pagination_endpoint()
    test_simplified_async()
    
    print("\n" + "="*80)
    if success:
        print("✅ Test completed - check the saved files!")
    print("="*80)

