"""
Use EXACT headers from user's DevTools - not simplified
"""

import sys, os, json, re, time
sys.path.insert(0, 'backend')
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from curl_cffi import requests as curl_requests

print('Capturing fresh callback with UC...\n')

options = uc.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = uc.Chrome(options=options)
driver.get('https://shopping.google.com/?hl=en&gl=us')
time.sleep(2)

search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'q')))
search_box.send_keys('milk')
search_box.send_keys(Keys.ENTER)

time.sleep(5)

for i in range(1, 6):
    driver.execute_script(f'window.scrollTo(0, {i * 800});')
    time.sleep(3)

print('Finding callback...\n')

logs = driver.get_log('performance')
callback_url = None

for entry in logs:
    try:
        message = json.loads(entry['message'])['message']
        if message['method'] == 'Network.requestWillBeSent':
            url = message['params']['request']['url']
            if '/async/callback' in url and 'google.com' in url:
                callback_url = url
                print(f'✅ Found: {url[:80]}...\n')
                break
    except:
        pass

if not callback_url:
    print('No callback found')
    driver.quit()
    exit(1)

# Get ALL cookies as dict
cookies = {}
for cookie in driver.get_cookies():
    cookies[cookie['name']] = cookie['value']

print(f'Captured {len(cookies)} cookies\n')

# Don't close driver yet - keep session alive!
print('Testing IMMEDIATELY with curl_cffi (driver still open)...\n')

# Use COMPLETE headers like a real browser
headers = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'referer': driver.current_url,  # Use actual current page as referer
    'sec-ch-ua': '"Chromium";v="120", "Google Chrome";v="120", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

r = curl_requests.get(
    callback_url,
    headers=headers,
    cookies=cookies,
    impersonate='chrome120',
    timeout=30
)

print(f'Status: {r.status_code}')
print(f'Size: {len(r.text):,}')

prices = re.findall(r'\$([0-9]+\.[0-9]{2})', r.text)
print(f'Prices: {len(prices)}')

if len(prices) > 10:
    print(f'\n🎉🎉🎉 ${prices[0]}, ${prices[1]}, ${prices[2]}')
    print('\n✅ IT WORKS WITH CORRECT HEADERS AND COOKIES!')
else:
    print(f'\nResponse: {r.text[:500]}')

driver.quit()

