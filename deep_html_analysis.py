from bs4 import BeautifulSoup
import re
import json

def analyze_response(filepath, name):
    """Deep analysis of HTML response"""
    
    print(f"\n{'='*80}")
    print(f"Analyzing: {name}")
    print('='*80)
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    
    print(f"File size: {len(html):,} characters")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Check for ANY elements with data- attributes
    print("\n1. Data attributes:")
    all_elements = soup.find_all()
    data_attrs = {}
    for elem in all_elements:
        for attr in elem.attrs:
            if attr.startswith('data-'):
                data_attrs[attr] = data_attrs.get(attr, 0) + 1
    
    if data_attrs:
        print("Found data attributes:")
        for attr, count in sorted(data_attrs.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {attr}: {count}")
            
            # If we find promising attributes, show examples
            if any(x in attr.lower() for x in ['doc', 'pck', 'price', 'product', 'merchant']):
                examples = soup.find_all(attrs={attr: True})[:2]
                for ex in examples:
                    val = ex.get(attr, '')
                    if val and len(str(val)) < 200:
                        print(f"    Example value: {val}")
    else:
        print("  No data- attributes found")
    
    # 2. Look for specific class patterns
    print("\n2. Google Shopping class patterns:")
    shopping_classes = [
        'sh-dgr__',
        'sh-dlr__',
        'sh-np__',
        'sh-pr__',
        'KZmu8e',  # Known Google Shopping classes
        'translate-rtl',
    ]
    
    for pattern in shopping_classes:
        elements = soup.find_all(class_=re.compile(pattern))
        if elements:
            print(f"  ✓ Found {len(elements)} elements with class containing '{pattern}'")
            if len(elements) > 0:
                print(f"    Example: {str(elements[0])[:150]}")
    
    # 3. Look for script tags with JSON
    print("\n3. Script tags analysis:")
    scripts = soup.find_all('script')
    print(f"  Total scripts: {len(scripts)}")
    
    json_like_scripts = []
    for script in scripts:
        if script.string:
            content = str(script.string)
            # Look for array of objects or object with arrays
            if re.search(r'\[{"', content) or re.search(r'{"[^"]+":.*\[', content):
                json_like_scripts.append(script)
    
    print(f"  Scripts with JSON-like content: {len(json_like_scripts)}")
    
    if json_like_scripts:
        # Analyze the largest one
        largest = max(json_like_scripts, key=lambda s: len(s.string))
        content = str(largest.string)
        
        print(f"\n  Largest script size: {len(content):,} chars")
        
        # Try to extract structured data
        # Look for common patterns
        patterns_to_check = [
            (r'"price"[:\s]+"?([0-9.]+)"?', 'prices'),
            (r'"title"[:\s]+"([^"]{10,100})"', 'titles'),
            (r'"merchant"[:\s]+"([^"]+)"', 'merchants'),
            (r'"seller"[:\s]+"([^"]+)"', 'sellers'),
            (r'"name"[:\s]+"([^"]{10,100})"', 'names'),
        ]
        
        found_data = {}
        for pattern, label in patterns_to_check:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                unique = list(set(matches))[:5]
                found_data[label] = unique
                print(f"  ✓ Found {label}: {unique}")
        
        if found_data:
            print("\n  🎉 EXTRACTABLE DATA FOUND!")
            return True
    
    # 4. Check for noscript content (fallback)
    print("\n4. Noscript content:")
    noscript = soup.find_all('noscript')
    if noscript:
        print(f"  Found {len(noscript)} noscript tags")
        for ns in noscript:
            if len(ns.get_text()) > 50:
                print(f"  Content preview: {ns.get_text()[:100]}")
    
    # 5. Check meta tags
    print("\n5. Meta tags:")
    og_tags = soup.find_all('meta', property=re.compile(r'og:'))
    if og_tags:
        print(f"  Found {len(og_tags)} OpenGraph tags")
        for tag in og_tags[:5]:
            prop = tag.get('property', '')
            content = tag.get('content', '')
            if content:
                print(f"    {prop}: {content[:100]}")
    
    # 6. Raw text search for prices
    print("\n6. Raw price patterns in HTML:")
    prices = re.findall(r'\$\d+\.?\d{0,2}', html)
    unique_prices = list(set(prices))[:10]
    if unique_prices:
        print(f"  Found prices: {unique_prices}")
    
    # 7. Look for store names
    print("\n7. Common store names:")
    stores = ['walmart', 'target', 'whole foods', 'kroger', 'safeway', 'amazon', 
              'costco', 'trader joe', 'sprouts', 'publix', 'wegmans']
    found_stores = [store for store in stores if store.lower() in html.lower()]
    if found_stores:
        print(f"  Found stores: {found_stores}")
    
    return False

if __name__ == "__main__":
    files = [
        ('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/api_response_2.html', 'Desktop Response'),
        ('/Users/spensercourville-taylor/htmlfiles/lowCostGroceries/mobile_response.html', 'Mobile Response'),
    ]
    
    found_parseable = False
    for filepath, name in files:
        try:
            result = analyze_response(filepath, name)
            if result:
                found_parseable = True
        except Exception as e:
            print(f"Error analyzing {name}: {e}")
    
    print("\n" + "="*80)
    if found_parseable:
        print("✓ FOUND PARSEABLE DATA - Can build scraper!")
    else:
        print("⚠️  No direct data - Need to check for AJAX endpoints or use lightweight headless")
    print("="*80)

