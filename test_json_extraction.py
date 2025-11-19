import requests
import json
import re
from bs4 import BeautifulSoup

def extract_embedded_json():
    """Try to extract any embedded JSON data from Google Shopping"""
    
    url = "https://www.google.com/search?q=milk&tbm=shop&tbs=local_avail:1,mr:1,sales:1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print("Searching for embedded JSON data in Google Shopping response...")
    print("="*80)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Response size: {len(response.text):,} bytes\n")
        
        # Method 1: Look for inline JavaScript with data
        # Google often embeds data in window.__ variables or AF_initDataCallback
        patterns = [
            r'AF_initDataCallback\((.*?)\);',
            r'window\._[a-zA-Z]+\s*=\s*(\{.*?\});',
            r'data:\s*(\{.*?\})',
        ]
        
        found_any = False
        for pattern in patterns:
            matches = re.findall(pattern, response.text, re.DOTALL)
            if matches:
                print(f"✓ Found {len(matches)} matches for pattern: {pattern[:50]}...")
                found_any = True
                
                # Try to parse first match
                for i, match in enumerate(matches[:3]):
                    try:
                        # Try to extract JSON-like structure
                        if '{' in match:
                            # Find the JSON object
                            start = match.find('{')
                            end = match.rfind('}') + 1
                            if end > start:
                                json_str = match[start:end]
                                data = json.loads(json_str)
                                print(f"\n  Sample {i+1} (parsed successfully):")
                                print(f"  Keys: {list(data.keys())[:10]}")
                                
                                # Save first successful parse
                                if i == 0:
                                    with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/extracted_json.json', 'w') as f:
                                        json.dump(data, f, indent=2)
                                    print("  ✓ Saved to extracted_json.json")
                    except Exception as e:
                        pass
        
        if not found_any:
            print("❌ No obvious JSON data patterns found")
        
        # Method 2: Look for specific Google Shopping data structures
        print("\n" + "="*80)
        print("Looking for Google Shopping specific patterns...")
        
        # Look for price patterns near product info
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        
        data_scripts = []
        for script in scripts:
            if script.string and len(script.string) > 1000:
                content = script.string
                # Look for product-like data
                if any(term in content for term in ['price', 'product', 'merchant', 'availability']):
                    data_scripts.append(script)
        
        print(f"Found {len(data_scripts)} scripts with product-related terms")
        
        if data_scripts:
            # Analyze the largest one
            largest = max(data_scripts, key=lambda s: len(s.string))
            content = largest.string
            
            print(f"\nAnalyzing largest script ({len(content):,} chars):")
            
            # Look for specific patterns
            checks = [
                ('price values (\\$\\d+)', re.findall(r'\$\d+\.?\d*', content)),
                ('USD amounts', re.findall(r'USD["\']?\s*:\s*["\']?(\d+\.?\d*)', content)),
                ('merchant/store names', re.findall(r'"merchant["\']?\s*:\s*["\']?([^"\']+)', content)),
                ('product titles', re.findall(r'"title["\']?\s*:\s*["\']?([^"\']{20,80})', content)),
            ]
            
            for name, results in checks:
                unique = list(set(results))[:5]
                if unique:
                    print(f"  ✓ {name}: {unique}")
        
        # Method 3: Check for any window.AF_initDataCallback calls
        print("\n" + "="*80)
        print("Checking for AF_initDataCallback (Google's data injection method)...")
        
        af_calls = re.findall(r'AF_initDataCallback\(\{[^}]+key:\s*["\']([^"\']+)', response.text)
        if af_calls:
            print(f"Found {len(af_calls)} AF_initDataCallback calls with keys:")
            for key in af_calls[:10]:
                print(f"  - {key}")
        else:
            print("❌ No AF_initDataCallback calls found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_embedded_json()
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("If AF_initDataCallback found → data is embedded but needs extraction")
    print("If no structured data found → requires full JavaScript rendering")
    print("="*80)

