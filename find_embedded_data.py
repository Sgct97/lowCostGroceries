import requests
from bs4 import BeautifulSoup
import json
import re

def find_embedded_json():
    """Look for JSON embedded in the initial HTML"""
    
    print("="*80)
    print("SEARCHING FOR EMBEDDED JSON IN HTML")
    print("="*80)
    
    url = "https://www.google.com/search"
    params = {'q': 'milk', 'tbm': 'shop'}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        html = response.text
        
        print(f"✅ Got HTML: {len(html):,} bytes\n")
        
        # 1. Look for window._ variables (Google's common pattern)
        print("1. Searching for window._ variables...")
        window_vars = re.findall(r'window\._[a-zA-Z0-9_]+\s*=\s*(\{.*?\});', html, re.DOTALL)
        print(f"   Found {len(window_vars)} window._ assignments")
        
        if window_vars:
            for i, var in enumerate(window_vars[:3]):
                try:
                    # Try to parse first 1000 chars
                    sample = var[:1000]
                    if 'price' in sample.lower() or 'product' in sample.lower():
                        print(f"   ✅ Found product data in window var {i}!")
                        print(f"   Sample: {sample[:200]}")
                except:
                    pass
        
        # 2. Look for AF_initDataCallback (Google's data injection)
        print("\n2. Searching for AF_initDataCallback...")
        callbacks = re.findall(r'AF_initDataCallback\((.*?)\);', html, re.DOTALL)
        print(f"   Found {len(callbacks)} AF_initDataCallback calls")
        
        if callbacks:
            for i, cb in enumerate(callbacks[:5]):
                if 'price' in cb.lower() or 'product' in cb.lower():
                    print(f"   ✅ Callback {i} contains product data!")
                    print(f"   Sample: {cb[:300]}")
                    
                    # Try to extract the data parameter
                    data_match = re.search(r'data:(.*?)(?:,sideChannel|,hash|\}$)', cb, re.DOTALL)
                    if data_match:
                        try:
                            json_str = data_match.group(1).strip()
                            # Save it
                            with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/callback_{i}.txt', 'w') as f:
                                f.write(json_str)
                            print(f"   💾 Saved to callback_{i}.txt")
                        except:
                            pass
        
        # 3. Look for inline <script> with JSON
        print("\n3. Searching inline script tags...")
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        
        json_scripts = []
        for script in scripts:
            if script.string:
                content = script.string
                # Look for large data structures with product terms
                if len(content) > 5000 and ('price' in content.lower() or 'product' in content.lower()):
                    json_scripts.append(content)
        
        print(f"   Found {len(json_scripts)} large scripts with product terms")
        
        if json_scripts:
            # Analyze the largest one
            largest = max(json_scripts, key=len)
            print(f"   Largest script: {len(largest):,} chars")
            
            # Try to extract JSON-like structures
            # Look for arrays or objects
            json_matches = re.findall(r'(\[\[.*?\]\]|\{.*?\})', largest[:10000], re.DOTALL)
            print(f"   Found {len(json_matches)} JSON-like structures")
            
            # Save the largest script
            with open('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/largest_script.js', 'w') as f:
                f.write(largest[:50000])  # First 50k chars
            print("   💾 Saved to largest_script.js")
        
        # 4. Look for specific Google Shopping data patterns
        print("\n4. Searching for Google Shopping data patterns...")
        
        # Look for data-docid, data-pck, etc
        patterns = {
            'data-docid': re.findall(r'data-docid="([^"]+)"', html),
            'data-pck': re.findall(r'data-pck="([^"]+)"', html),
            'data-pri': re.findall(r'data-pri="([^"]+)"', html),
            'data-price': re.findall(r'data-price="([^"]+)"', html),
        }
        
        for name, matches in patterns.items():
            if matches:
                print(f"   ✅ Found {len(matches)} {name} attributes")
                print(f"      Sample: {matches[0]}")
        
        # 5. Look for encoded/base64 data
        print("\n5. Searching for encoded data...")
        
        # Look for data:application/json
        json_data = re.findall(r'data:application/json[^"\']*?([A-Za-z0-9+/=]{100,})', html)
        if json_data:
            print(f"   ✅ Found {len(json_data)} base64-encoded JSON blobs")
        
        # 6. Extract ALL JavaScript variables that might contain data
        print("\n6. Extracting all large JavaScript variables...")
        
        # Pattern: var name = large_object or const name = large_object
        var_pattern = r'(?:var|const|let)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(\[.*?\]|\{.*?\});'
        variables = re.findall(var_pattern, html, re.DOTALL)
        
        large_vars = [(name, val) for name, val in variables if len(val) > 1000]
        print(f"   Found {len(large_vars)} large JavaScript variables")
        
        for name, value in large_vars[:3]:
            if 'price' in value.lower() or 'product' in value.lower():
                print(f"   ✅ Variable '{name}' contains product data!")
                with open(f'/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/var_{name}.txt', 'w') as f:
                    f.write(value[:10000])
                print(f"   💾 Saved to var_{name}.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_post_requests():
    """Check if there are POST endpoints in the page"""
    
    print("\n" + "="*80)
    print("SEARCHING FOR POST REQUEST PATTERNS")
    print("="*80)
    
    url = "https://www.google.com/search"
    params = {'q': 'milk', 'tbm': 'shop'}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        html = response.text
        
        # Look for fetch() or XHR patterns with POST
        post_patterns = [
            r'fetch\(["\']([^"\']+)["\'],\s*\{[^}]*method:\s*["\']POST["\']',
            r'\.post\(["\']([^"\']+)["\']',
            r'XMLHttpRequest.*open\(["\']POST["\'],\s*["\']([^"\']+)["\']',
        ]
        
        found_endpoints = set()
        for pattern in post_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            found_endpoints.update(matches)
        
        if found_endpoints:
            print(f"✅ Found {len(found_endpoints)} POST endpoints in JavaScript:")
            for endpoint in sorted(found_endpoints)[:10]:
                print(f"   - {endpoint}")
        else:
            print("   No POST endpoints found in page source")
        
        # Look for f.req patterns
        print("\n   Searching for f.req (Google RPC format)...")
        freq_matches = re.findall(r'f\.req[^&]*', html)
        if freq_matches:
            print(f"   ✅ Found {len(freq_matches)} f.req patterns")
            for match in freq_matches[:3]:
                print(f"      {match[:100]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║              DEEP SEARCH FOR EMBEDDED DATA                               ║
    ║              (POST requests + Embedded JSON)                             ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    find_embedded_json()
    find_post_requests()
    
    print("\n" + "="*80)
    print("SUMMARY:")
    print("Check the saved files (callback_*.txt, largest_script.js, var_*.txt)")
    print("for actual product data!")
    print("="*80)

