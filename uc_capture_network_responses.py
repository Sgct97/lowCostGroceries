"""
Capture actual network RESPONSE bodies from UC
The prices are in async responses, not page_source!
"""

import sys
import os
import json
import re
import time
import base64

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("\n" + "="*80)
print("CAPTURING NETWORK RESPONSE BODIES FROM UC")
print("="*80 + "\n")

# Enable performance logging AND response body capture
options = uc.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = uc.Chrome(options=options)

# Enable Network domain to capture response bodies
driver.execute_cdp_cmd('Network.enable', {})

print("Searching for 'milk'...\n")
driver.get('https://shopping.google.com/?hl=en&gl=us')

search_box = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, 'q'))
)
search_box.send_keys('milk')
search_box.send_keys(Keys.ENTER)

print("Waiting and scrolling...\n")
time.sleep(3)

for i in range(1, 4):
    driver.execute_script(f"window.scrollTo(0, {i * 800});")
    time.sleep(2)

print("Analyzing network logs...\n")

logs = driver.get_log('performance')

# Find requests with 'q=milk' or 'async'
relevant_requests = []

for entry in logs:
    try:
        message = json.loads(entry['message'])['message']
        
        if message['method'] == 'Network.responseReceived':
            response = message['params']['response']
            url = response['url']
            request_id = message['params']['requestId']
            
            # Look for search-related requests
            if ('q=milk' in url or 'async' in url or 'search?' in url) and 'google.com' in url:
                relevant_requests.append({
                    'url': url[:100],
                    'request_id': request_id,
                    'mime_type': response.get('mimeType', ''),
                    'status': response.get('status', 0)
                })
    except:
        pass

print(f"Found {len(relevant_requests)} relevant requests\n")

# Try to get response bodies
prices_found = 0

for i, req in enumerate(relevant_requests[:10]):  # Check first 10
    print(f"\nRequest {i+1}:")
    print(f"  URL: {req['url']}...")
    print(f"  Status: {req['status']}, Type: {req['mime_type']}")
    
    try:
        # Get response body
        response_body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': req['request_id']})
        
        body = response_body.get('body', '')
        
        # If base64 encoded
        if response_body.get('base64Encoded'):
            body = base64.b64decode(body).decode('utf-8', errors='ignore')
        
        # Look for prices
        prices = re.findall(r'\$([0-9]+\.[0-9]{2})', body)
        
        print(f"  Body size: {len(body):,} bytes")
        print(f"  Prices found: {len(prices)}")
        
        if len(prices) > 0:
            print(f"  ✅ PRICES: ${prices[0]}, ${prices[1] if len(prices)>1 else '...'}, ...")
            prices_found += len(prices)
            
            # Save this response
            with open(f'network_response_{i}.html', 'w', encoding='utf-8') as f:
                f.write(body[:50000])  # First 50KB
            print(f"  Saved to: network_response_{i}.html")
        
    except Exception as e:
        print(f"  ❌ Could not get body: {str(e)[:50]}")

print("\n" + "="*80)
print("RESULTS")
print("="*80)

print(f"\nTotal prices found in network responses: {prices_found}")

if prices_found > 50:
    print("\n🎉🎉🎉 SUCCESS! UC CAN ACCESS PRICE DATA!")
    print("✅ Prices are in async network responses")
    print("✅ We just need to capture the right responses")
    print("✅ This proves the hybrid approach CAN work!")
else:
    print("\n⚠️  Limited or no price data captured")
    print("May need different approach to response capture")

driver.quit()

