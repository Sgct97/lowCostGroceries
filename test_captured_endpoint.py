import requests
import json
import sys

"""
QUICK ENDPOINT TESTER

Once you capture a cURL from Chrome DevTools:
1. Paste the cURL command in CURL_COMMAND below (or as command line arg)
2. Run this script
3. It will convert to Python and test it

Example cURL format:
curl 'https://www.google.com/some/endpoint?q=milk' \
  -H 'authority: www.google.com' \
  -H 'accept: application/json' \
  --compressed
"""

def curl_to_python(curl_command):
    """Convert cURL to Python requests (basic parser)"""
    
    # Extract URL
    url_match = re.search(r"curl\s+'([^']+)'", curl_command)
    if not url_match:
        url_match = re.search(r'curl\s+"([^"]+)"', curl_command)
    if not url_match:
        url_match = re.search(r'curl\s+([^\s]+)', curl_command)
    
    if not url_match:
        print("❌ Couldn't extract URL from cURL")
        return None, None
    
    url = url_match.group(1)
    
    # Extract headers
    headers = {}
    header_pattern = r"-H\s+'([^:]+):\s*([^']+)'"
    for match in re.finditer(header_pattern, curl_command):
        key, value = match.groups()
        headers[key.strip()] = value.strip()
    
    # Also try double quotes
    header_pattern2 = r'-H\s+"([^:]+):\s*([^"]+)"'
    for match in re.finditer(header_pattern2, curl_command):
        key, value = match.groups()
        headers[key.strip()] = value.strip()
    
    return url, headers

def test_endpoint_manually():
    """Test with manually pasted cURL or endpoint details"""
    
    print("="*80)
    print("TESTING CAPTURED ENDPOINT")
    print("="*80)
    
    # PASTE YOUR cURL HERE (or endpoint details)
    # Example formats:
    
    # Option 1: Just test a specific endpoint directly
    test_configs = [
        {
            'name': 'Shopping Mobile API',
            'url': 'https://shopping.google.com/m/search',
            'params': {'q': 'milk', 'hl': 'en', 'gl': 'us'},
            'headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
                'Accept': 'application/json',
            }
        },
        {
            'name': 'Shopping Search API',
            'url': 'https://www.google.com/search',
            'params': {
                'q': 'milk',
                'tbm': 'shop',
                'hl': 'en',
                'sxsrf': '',  # Security token (may need to capture)
            },
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Accept': 'text/html,application/xhtml+xml',
                'X-Client-Data': '',  # May be required
            }
        }
    ]
    
    for config in test_configs:
        print(f"\n{'='*80}")
        print(f"Testing: {config['name']}")
        print(f"URL: {config['url']}")
        print('='*80)
        
        try:
            response = requests.get(
                config['url'],
                params=config['params'],
                headers=config['headers'],
                timeout=10
            )
            
            print(f"✅ Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Size: {len(response.text):,} bytes")
            
            # Try to parse as JSON
            if 'json' in response.headers.get('Content-Type', '').lower():
                try:
                    data = response.json()
                    print("\n🎉 SUCCESS! Got JSON response:")
                    print(json.dumps(data, indent=2)[:1000])
                    
                    # Save it
                    filename = f"/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/working_endpoint_{config['name'].replace(' ', '_')}.json"
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"\n💾 Saved to: {filename}")
                    
                except:
                    pass
            
            # Check for product data
            sample = response.text[:2000].lower()
            indicators = ['price', 'product', 'merchant', 'offer', 'availability']
            found = [ind for ind in indicators if ind in sample]
            
            if found:
                print(f"\n✅ Found product indicators: {found}")
                
                # Save sample
                filename = f"/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/promising_{config['name'].replace(' ', '_')}.txt"
                with open(filename, 'w') as f:
                    f.write(response.text[:5000])
                print(f"💾 Saved sample to: {filename}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def paste_curl_here():
    """
    If you have a cURL command from Chrome DevTools, paste it below as a string
    """
    
    # PASTE YOUR CURL HERE:
    curl_command = """
    
    # Example (replace with your actual cURL):
    # curl 'https://www.google.com/shopping/api?q=milk' \
    #   -H 'accept: application/json' \
    #   -H 'cookie: ...' \
    #   --compressed
    
    """
    
    if curl_command.strip() and not curl_command.strip().startswith('#'):
        print("\n" + "="*80)
        print("TESTING YOUR PASTED cURL")
        print("="*80)
        
        try:
            import re
            url, headers = curl_to_python(curl_command)
            
            if url:
                print(f"Extracted URL: {url}")
                print(f"Extracted Headers: {len(headers)} headers")
                
                response = requests.get(url, headers=headers, timeout=10)
                print(f"\nStatus: {response.status_code}")
                print(f"Response preview:\n{response.text[:500]}")
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\n⚠️  No cURL pasted. Use manual test configs above.")

if __name__ == "__main__":
    import re
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                   GOOGLE SHOPPING ENDPOINT TESTER                        ║
    ║                                                                          ║
    ║  INSTRUCTIONS:                                                           ║
    ║  1. Open Chrome → DevTools → Network Tab                                ║
    ║  2. Go to google.com/search?q=milk&tbm=shop                             ║
    ║  3. Find XHR/Fetch requests with product data                           ║
    ║  4. Right-click → Copy → Copy as cURL                                   ║
    ║  5. Paste it in the curl_command variable in this script                ║
    ║  6. Re-run the script                                                   ║
    ║                                                                          ║
    ║  OR: Just tell me the endpoint URL you found and I'll test it           ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    test_endpoint_manually()
    paste_curl_here()
    
    print("\n" + "="*80)
    print("💡 TIP: Once we find the working endpoint, scraping will be:")
    print("   - 50x faster than browser automation")
    print("   - Much more reliable")
    print("   - Easier to scale")
    print("="*80)

