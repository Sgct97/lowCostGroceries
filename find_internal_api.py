import requests
import json
import re
from urllib.parse import quote

def test_shopping_api_endpoints():
    """Test potential internal Google Shopping API endpoints"""
    
    print("="*80)
    print("FINDING GOOGLE SHOPPING INTERNAL API")
    print("="*80)
    
    query = "organic milk"
    location = "10001"  # NYC ZIP
    
    # Common headers that Google APIs expect
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Origin': 'https://www.google.com',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    # Known Google Shopping API patterns (from reverse engineering)
    test_endpoints = [
        {
            'name': 'Shopping API v1',
            'url': 'https://www.google.com/shopping/api/v1/products',
            'params': {'q': query, 'location': location, 'hl': 'en', 'gl': 'us'}
        },
        {
            'name': 'Async Shopping Data',
            'url': 'https://www.google.com/async/eshop',
            'params': {'q': query, 'tbm': 'shop', 'async': 'search_q:'+query}
        },
        {
            'name': 'Shopping Search Internal',
            'url': 'https://www.google.com/_/shopping/_/search',
            'params': {'q': query, 'hl': 'en'}
        },
        {
            'name': 'Shopping RPC',
            'url': 'https://www.google.com/_/shopping/_/rpc/ShoppingService.Search',
            'params': {}
        },
        {
            'name': 'Gen 204 (Analytics/Data)',
            'url': 'https://www.google.com/gen_204',
            'params': {'atyp': 'csi', 'ei': 'test', 's': 'shopping'}
        },
        {
            'name': 'Shopping PSY (Suggestions)',
            'url': 'https://www.google.com/complete/search',
            'params': {'q': query, 'client': 'psy-ab', 'tbm': 'shop'}
        },
    ]
    
    for endpoint in test_endpoints:
        print(f"\n{'='*80}")
        print(f"Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        print('='*80)
        
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], 
                                   headers=headers, timeout=10, allow_redirects=True)
            
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"Response size: {len(response.text):,} bytes")
            
            # Check if it's JSON
            if 'application/json' in response.headers.get('Content-Type', ''):
                try:
                    data = response.json()
                    print("✅ VALID JSON RESPONSE!")
                    print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Array'}")
                    
                    # Save it
                    filename = f"api_response_{endpoint['name'].replace(' ', '_')}.json"
                    with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/{filename}', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"💾 Saved to {filename}")
                    
                except json.JSONDecodeError:
                    print("⚠️ JSON decode failed")
            
            # Check for product indicators
            if any(term in response.text.lower() for term in ['product', 'price', 'merchant', 'offer']):
                print("✅ Contains product-related data!")
                
                # Look for structured data
                if '"price"' in response.text or '"products"' in response.text:
                    print("🎯 FOUND PRODUCT/PRICE DATA!")
                    
                    # Save for analysis
                    with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/found_endpoint_{endpoint["name"].replace(" ", "_")}.txt', 'w') as f:
                        f.write(response.text[:5000])
                    print("💾 Saved sample response")
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")

def test_shopping_graphql():
    """Test if Google Shopping uses GraphQL"""
    
    print(f"\n{'='*80}")
    print("Testing GraphQL Endpoint")
    print('='*80)
    
    url = "https://www.google.com/shopping/_/graphql"
    
    # Sample GraphQL query
    query_gql = """
    query SearchProducts($query: String!) {
        products(query: $query) {
            title
            price
            merchant
        }
    }
    """
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    
    payload = {
        'query': query_gql,
        'variables': {'query': 'milk'}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ GraphQL endpoint exists!")
            print(response.text[:500])
    except Exception as e:
        print(f"No GraphQL: {str(e)[:50]}")

def test_protobuf_endpoint():
    """Google often uses Protocol Buffers for internal APIs"""
    
    print(f"\n{'='*80}")
    print("Testing Protocol Buffer Endpoints")
    print('='*80)
    
    # Google's RPC endpoints often use this pattern
    url = "https://www.google.com/_/shopping/_/rpc"
    
    headers = {
        'Content-Type': 'application/x-protobuf',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'X-Goog-Api-Key': 'AIzaSyB...test',  # Would need real key
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code != 404:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Not available: {str(e)[:50]}")

def manual_capture_instructions():
    """Provide instructions to manually capture the endpoint"""
    
    print(f"\n{'='*80}")
    print("MANUAL ENDPOINT DISCOVERY INSTRUCTIONS")
    print('='*80)
    
    instructions = """
    If automated tests didn't find the endpoint, here's how to find it:
    
    1. Open Chrome in Incognito mode
    2. Open DevTools (F12 or Cmd+Option+I)
    3. Go to Network tab
    4. Check "Preserve log"
    5. Filter: XHR or Fetch
    6. Navigate to: https://www.google.com/search?q=milk&tbm=shop
    7. Wait for page to load
    8. Look for requests that:
       - Return JSON data
       - Have "shopping", "product", or "search" in the URL
       - Show product data in the Preview/Response tab
    
    9. When you find the right request:
       - Right-click → Copy → Copy as cURL
       - Paste it here and I'll convert it to Python
    
    Common Google API patterns to look for:
       - /_/shopping/_/...
       - /async/...
       - /gen_204?...
       - /s?q=...
       - /xjs/_/...
    
    The endpoint might also be in:
       - shopping.google.com (not www.google.com)
       - /m/search (mobile version)
       - /api/shopping/...
    """
    
    print(instructions)

if __name__ == "__main__":
    print("🔍 REVERSE ENGINEERING GOOGLE SHOPPING API")
    print("(The RIGHT way to scrape - like you did with Google Maps)")
    print()
    
    test_shopping_api_endpoints()
    test_shopping_graphql()
    test_protobuf_endpoint()
    manual_capture_instructions()
    
    print("\n" + "="*80)
    print("NEXT STEP:")
    print("Run this script, then follow the manual instructions if needed.")
    print("Once we find the endpoint, we'll have 10x faster scraping than Playwright!")
    print("="*80)

