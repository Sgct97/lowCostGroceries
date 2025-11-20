"""
Open UC and keep it running for manual DevTools inspection
User will check if price data appears in network Response tabs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("\n" + "="*80)
print("UC MANUAL DEVTOOLS INSPECTION")
print("="*80 + "\n")

# Enable performance logging to capture network
options = uc.ChromeOptions()
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = uc.Chrome(options=options)

print("Opening Google Shopping with UC...\n")
driver.get('https://shopping.google.com/?hl=en&gl=us')

print("Searching for 'milk'...\n")
search_box = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, 'q'))
)
search_box.send_keys('milk')
search_box.send_keys(Keys.ENTER)

print("Waiting for page to load...\n")
time.sleep(3)

print("Scrolling to trigger network requests...\n")
for i in range(1, 6):
    driver.execute_script(f"window.scrollTo(0, {i * 800});")
    time.sleep(2)

print("\n" + "="*80)
print("INSTRUCTIONS:")
print("="*80)
print("\n1. Open Chrome DevTools (Right-click → Inspect)")
print("2. Go to Network tab")
print("3. Search for 'q=milk' in the filter")
print("4. Click on any request that has 'async' or 'search' in the URL")
print("5. Go to Response tab")
print("6. Search for '$' in the response")
print("\nQUESTION: Do you see dollar prices in the Response tab?")
print("\nIf YES → UC can get prices, we missed something in our code")
print("If NO → Google blocks/limits UC, explains our failures")
print("\n" + "="*80)

print("\n\nKeeping browser open for 2 minutes for inspection...")
print("(Browser will auto-close after 2 minutes)\n")

time.sleep(120)

driver.quit()
print("\nBrowser closed.")

