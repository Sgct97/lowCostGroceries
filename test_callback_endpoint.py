import requests
import json
import re

def test_callback_endpoint():
    """Test the /async/callback endpoint"""
    
    print("="*80)
    print("TESTING /async/callback ENDPOINT")
    print("="*80)
    
    # The URL from your fetch
    url = "https://www.google.com/async/callback:6948"
    
    # Extract key parameters
    params = {
        'fc': 'EvcCCrcCQUxrdF92R2wzYmNoR3dyM3FNS0pJUU1pdUU1M0x4b195X2pzTUMwcy1Qekc4N0RGbXEyYnozQk9RdEZBMml2WWpNM2VBakVRM2FVSXU0eVc1TGpRazBlNVA2S1JYRXREYmlzVTRzcWRvR3hDYkVqam9mMTZ6eDFIVWFzZktGNVJueWgtelFmdjl2OS1BZXd6QkdYV3kzNEJzUzIzeVhpUnBjZGJ3d0hvYmtyMmlvNS1qUU1VZXZVMTROSWZoYTU0NjBnY3pnNnBtVENTR3NHc1N1OThqWEo1elpTRmNsa1kzYjR3ZXhLUEt3MzNmN01NR3BIR0laMGlMQTlBTlBRMTZMN000eERnelJzQkdWYnZRa2k4LXhub1R6RERwSUk1MEVvYmx4LUh2OXRQTnMzbWxkaFFFbUUSF1JHa1dhZURWTXRiVjVOb1A0NVNhOEFFGiJBRk1BR0dxNXQybmRwVldHQ3BWenl0blBqbDJYejdYUGRB',
        'fcv': '3',
        'vet': '12ahUKEwjgh5q-o_CQAxXWKlkFHWOKBh4Q9pcOegQIBhAB..i',
        'ei': 'RGkWaeDVMtbV5NoP45Sa8AE',
        'opi': '95576897',
        'sca_esv': '4af503ebc609abd2',
        'shopmd': '1',
        'udm': '28',
        'yv': '3',
        'cs': '0',
        'async': '_fmt:prog,_id:fc_RGkWaeDVMtbV5NoP45Sa8AE_1'
    }
    
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
    print(f"Key params: fc={params['fc'][:50]}...")
    print("\n" + "="*80)
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        print(f"✅ Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response size: {len(response.text):,} bytes")
        
        if response.status_code == 200:
            # Save response
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/callback_response.txt', 'w') as f:
                f.write(response.text)
            print("💾 Saved to: callback_response.txt")
            
            # Check for XSSI protection
            content = response.text
            if content.startswith(')]}\''):
                print("\n✅ Found XSSI protection prefix - API response!")
                content = content[4:]
            
            # Try to parse as JSON
            try:
                data = json.loads(content)
                print("\n🎉 SUCCESS! Got JSON!")
                print(f"Type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"Array length: {len(data)}")
                    if data:
                        print(f"First element type: {type(data[0])}")
                
                # Save JSON
                with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/callback_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print("💾 Saved JSON to: callback_data.json")
                
                # Look for product data
                json_str = json.dumps(data)
                keywords = ['price', 'product', 'title', 'merchant', 'store']
                found = [k for k in keywords if k in json_str.lower()]
                
                if found:
                    print(f"\n✅ FOUND PRODUCT DATA! Keywords: {found}")
                    
                    # Count occurrences
                    for keyword in found:
                        count = json_str.lower().count(keyword)
                        print(f"   '{keyword}': {count} occurrences")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"\n⚠️ Not standard JSON: {str(e)[:100]}")
                
                # Check for product terms anyway
                sample = response.text[:1000].lower()
                if any(term in sample for term in ['price', 'product', 'merchant']):
                    print("✅ But contains product-related terms!")
                    print(f"Sample: {response.text[:500]}")
            
            # Look for HTML with product data
            if '<' in response.text and '>' in response.text:
                print("\n📄 Response is HTML")
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Count product indicators
                prices = soup.find_all(string=re.compile(r'\$\d+'))
                links = soup.find_all('a')
                images = soup.find_all('img')
                
                print(f"   Prices: {len(prices)}")
                print(f"   Links: {len(links)}")
                print(f"   Images: {len(images)}")
                
                if len(prices) > 0:
                    print(f"\n✅ FOUND {len(prices)} PRICES!")
                    for price in prices[:5]:
                        print(f"      {price}")
        
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                TESTING THE CALLBACK ENDPOINT!                            ║
    ║                (This might be it!)                                       ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    test_callback_endpoint()
    
    print("\n" + "="*80)
    print("Check callback_response.txt and callback_data.json for results!")
    print("="*80)

