"""
Intercept network responses AS they happen
This is how we can capture the price data the user saw
"""

import sys
import os
import json
import re
import time
import base64
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("\n" + "="*80)
print("INTERCEPTING NETWORK RESPONSES IN REAL-TIME")
print("="*80 + "\n")

options = uc.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = uc.Chrome(options=options)

# Enable Network domain for response interception
driver.execute_cdp_cmd('Network.enable', {})

# Storage for captured responses
captured_responses = []

print("Navigating to Google Shopping...\n")
driver.get('https://shopping.google.com/?hl=en&gl=us')

# Wait a bit for initial load
time.sleep(2)

print("Starting search and capturing responses...\n")

search_box = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, 'q'))
)
search_box.send_keys('milk')
search_box.send_keys(Keys.ENTER)

# Wait for responses to come in
print("Waiting 3 seconds for responses...")
time.sleep(3)

# Scroll to trigger more
print("Scrolling...")
for i in range(1, 3):
    driver.execute_script(f"window.scrollTo(0, {i * 800});")
    time.sleep(2)

print("\nAnalyzing captured network traffic...\n")

# Parse performance logs
logs = driver.get_log('performance')

request_data = {}

for entry in logs:
    try:
        message = json.loads(entry['message'])['message']
        method = message['method']
        
        if method == 'Network.responseReceived':
            params = message['params']
            request_id = params['requestId']
            response = params['response']
            url = response['url']
            
            if 'google.com' in url and ('search?' in url or 'async' in url):
                request_data[request_id] = {
                    'url': url,
                    'status': response.get('status'),
                    'mime_type': response.get('mimeType', '')
                }
        
        # Try to capture response data
        elif method == 'Network.dataReceived':
            request_id = message['params']['requestId']
            if request_id in request_data:
                # Mark that data was received
                request_data[request_id]['has_data'] = True
                
    except:
        pass

# Now get the actual page HTML which should have the prices loaded
print("Getting final page HTML after all responses loaded...\n")
final_html = driver.page_source

# Parse for prices
prices = re.findall(r'\$([0-9]+\.[0-9]{2})', final_html)

print("="*80)
print("RESULTS")
print("="*80)

print(f"\nRequests found: {len(request_data)}")
print(f"Prices in final HTML: {len(prices)}")

if len(prices) > 50:
    print(f"\n🎉 SUCCESS! {len(prices)} prices captured!")
    print(f"Sample prices: ${prices[0]}, ${prices[1]}, ${prices[2]}, ...")
    print("\n✅ The page_source HAS the prices after waiting!")
    print("✅ Our sequential approach WAS working")
    print("✅ Issue: We weren't waiting long enough OR parsing correctly")
else:
    print("\n⚠️  Only found", len(prices), "prices")
    
    # Save HTML for inspection
    with open('final_page_for_inspection.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    print("\nSaved HTML to: final_page_for_inspection.html")
    print("Check this file - does it have price data?")

driver.quit()

