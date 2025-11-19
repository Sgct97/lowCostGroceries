import requests
import json
import re

def test_google_shopping_api():
    """Test the ACTUAL Google Shopping API endpoint you discovered"""
    
    print("="*80)
    print("TESTING REAL GOOGLE SHOPPING API ENDPOINT")
    print("="*80)
    
    # The endpoint you found
    url = "https://www.google.com/async/bgasy"
    
    # Key parameters from your cURL
    params = {
        'ei': 'ykUWacXEL5On5NoPhpDgsA4',  # Event ID (can be generated)
        'yv': '3',
        'cs': '0',
        'async': '_fmt:jspb',  # IMPORTANT: JavaScript Protocol Buffer format
        'shopmd': '1',  # Shopping mode
        'udm': '28',  # Universal Data Model - Shopping (28 = shopping)
    }
    
    # Essential headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    print(f"\nURL: {url}")
    print(f"Params: {params}")
    print("\n" + "="*80)
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response Size: {len(response.text):,} bytes")
        
        if response.status_code == 200:
            # Save raw response
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/shopping_api_response.txt', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Saved raw response to: shopping_api_response.txt")
            
            # Check for XSSI protection (like Maps API)
            content = response.text
            if content.startswith(')]}\''):
                print("\n✅ Found XSSI protection prefix )]}' (just like Maps API!)")
                content = content[4:]  # Remove protection prefix
            
            # Try to parse as JSON
            try:
                data = json.loads(content)
                print("\n🎉 SUCCESS! Valid JSON response!")
                print(f"Data type: {type(data)}")
                
                if isinstance(data, list):
                    print(f"Array length: {len(data)}")
                elif isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                
                # Save parsed JSON
                with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/shopping_api_parsed.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("💾 Saved parsed JSON to: shopping_api_parsed.json")
                
                # Look for product data
                json_str = json.dumps(data)
                indicators = {
                    'price': json_str.count('"price"'),
                    'product': json_str.count('"product"'),
                    'merchant': json_str.count('"merchant"'),
                    'title': json_str.count('"title"'),
                }
                
                print("\n📊 Product Data Indicators:")
                for key, count in indicators.items():
                    if count > 0:
                        print(f"  ✅ Found '{key}': {count} occurrences")
                
            except json.JSONDecodeError as e:
                print(f"\n⚠️ Not standard JSON: {str(e)[:100]}")
                print("Might be Protocol Buffer or nested format")
                
                # Look for product data in raw text
                if any(term in content.lower() for term in ['price', 'product', 'merchant']):
                    print("✅ But contains product-related terms!")
                
                # Show sample
                print(f"\nFirst 500 chars:\n{content[:500]}")
            
            return True
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_search_query():
    """Test with an actual search query for milk"""
    
    print("\n" + "="*80)
    print("TESTING WITH SEARCH QUERY: 'milk'")
    print("="*80)
    
    url = "https://www.google.com/async/bgasy"
    
    # We need to figure out how to pass the search query
    # Options: Could be in 'q' param, or might need to be in the page state
    
    params = {
        'yv': '3',
        'cs': '0',
        'async': '_fmt:jspb',
        'shopmd': '1',
        'udm': '28',
        'q': 'milk',  # Try adding query
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.google.com/search?q=milk&tbm=shop',  # Important: shows we came from shopping search
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Size: {len(response.text):,} bytes")
        
        if response.status_code == 200 and len(response.text) > 100:
            print("✅ Got response with query parameter")
            
            # Save it
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/shopping_with_query.txt', 'w') as f:
                f.write(response.text[:2000])
            print("💾 Saved to: shopping_with_query.txt")
            
    except Exception as e:
        print(f"Error: {e}")

def analyze_url_pattern():
    """Analyze the URL pattern to understand parameters"""
    
    print("\n" + "="*80)
    print("UNDERSTANDING THE API PATTERN")
    print("="*80)
    
    analysis = """
    Key Parameters Found:
    
    1. udm=28
       - Universal Data Model
       - 28 = Shopping mode (similar to tbm=shop)
    
    2. async=_fmt:jspb
       - Format: JavaScript Protocol Buffer
       - This is what returns the actual data
    
    3. shopmd=1
       - Shopping mode enabled
    
    4. yv=3
       - Version parameter
    
    To scrape products, we likely need to:
    - Start at: google.com/search?q=QUERY&tbm=shop
    - Extract the state/session parameters
    - Then call /async/bgasy with those params
    - Parse the jspb response
    
    OR - Reverse engineer what params are needed directly
    """
    
    print(analysis)

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                   TESTING YOUR DISCOVERED ENDPOINT!                      ║
    ║                   /async/bgasy with _fmt:jspb                           ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    success = test_google_shopping_api()
    
    if success:
        test_with_search_query()
    
    analyze_url_pattern()
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("1. Check the saved response files")
    print("2. If we got data, I'll build the parser")
    print("3. If we need more params, check the page source for state data")
    print("="*80)

