#!/usr/bin/env python3
"""
PROVE that we can extract 'Nearby, X mi' and 'Pick up today' data
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import re

def test_nearby_data(zip_code="33773"):
    """Test extracting nearby and pickup data"""
    print(f"\n{'='*80}")
    print(f"PROVING Nearby/Pickup Data Extraction for ZIP {zip_code}")
    print(f"{'='*80}")
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Don't use headless - let it render fully
    # options.add_argument("--headless=new")
    
    driver = uc.Chrome(options=options, use_subprocess=False)
    
    try:
        # Search for "milk nearby" to trigger nearby results
        search_query = "milk nearby"
        url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&udm=28"
        
        print(f"\n✓ Loading: {url}")
        driver.get(url)
        time.sleep(5)  # Let page fully load
        
        # Try to click the "Nearby" filter
        print(f"\n✓ Looking for 'Nearby' filter to click...")
        try:
            # Try multiple selectors
            nearby_clicked = False
            
            # Method 1: Find by text
            nearby_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Nearby')]")
            for button in nearby_buttons:
                if button.is_displayed():
                    print(f"✓ Found visible 'Nearby' element: {button.tag_name}")
                    try:
                        button.click()
                        print(f"✓ Clicked 'Nearby' filter!")
                        nearby_clicked = True
                        time.sleep(5)  # Wait for filtered results
                        break
                    except Exception as e:
                        print(f"⚠️  Could not click {button.tag_name}: {e}")
            
            if not nearby_clicked:
                print("⚠️  Could not click 'Nearby' filter - results may not be filtered")
                
        except Exception as e:
            print(f"⚠️  Error with Nearby filter: {e}")
        
        # Take screenshot AFTER clicking
        driver.save_screenshot("nearby_screenshot.png")
        print(f"✓ Saved screenshot: nearby_screenshot.png")
        
        # Get the HTML
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save HTML
        with open("nearby_page_source.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✓ Saved HTML: nearby_page_source.html")
        
        # Strategy 1: Look for text containing "Nearby" with distance
        print("\n" + "="*80)
        print("STRATEGY 1: Search for 'Nearby' + 'mi' text")
        print("="*80)
        
        # Find all text nodes
        all_text = soup.get_text()
        
        # Use regex to find "Nearby, X mi" patterns
        nearby_pattern = r'Nearby,?\s*\d+\s*mi'
        nearby_matches = re.findall(nearby_pattern, all_text, re.IGNORECASE)
        
        if nearby_matches:
            print(f"\n✅ Found {len(nearby_matches)} 'Nearby, X mi' mentions:")
            for match in set(nearby_matches):
                print(f"  • {match}")
        else:
            print("\n❌ No 'Nearby, X mi' found in page text")
        
        # Strategy 2: Look for "Pick up" text
        print("\n" + "="*80)
        print("STRATEGY 2: Search for 'Pick up' text")
        print("="*80)
        
        pickup_pattern = r'Pick\s+up\s+\w+'
        pickup_matches = re.findall(pickup_pattern, all_text, re.IGNORECASE)
        
        if pickup_matches:
            print(f"\n✅ Found {len(pickup_matches)} 'Pick up' mentions:")
            for match in set(pickup_matches):
                print(f"  • {match}")
        else:
            print("\n❌ No 'Pick up' found in page text")
        
        # Strategy 3: Look at visible elements with specific classes/attributes
        print("\n" + "="*80)
        print("STRATEGY 3: Check for common badge/label classes")
        print("="*80)
        
        # Common classes for badges
        badge_classes = ['badge', 'label', 'tag', 'chip', 'pill']
        badge_elements = []
        
        for badge_class in badge_classes:
            elements = soup.find_all(class_=re.compile(badge_class, re.IGNORECASE))
            badge_elements.extend(elements)
        
        if badge_elements:
            print(f"\n✓ Found {len(badge_elements)} badge-like elements")
            for elem in badge_elements[:10]:
                text = elem.get_text(strip=True)
                if 'nearby' in text.lower() or 'pick' in text.lower() or 'mi' in text.lower():
                    print(f"  • {elem.name}.{elem.get('class')}: {text[:80]}")
        
        # Strategy 4: Look at ALL spans (often used for badges)
        print("\n" + "="*80)
        print("STRATEGY 4: Search all <span> elements")
        print("="*80)
        
        all_spans = soup.find_all('span')
        relevant_spans = []
        
        for span in all_spans:
            text = span.get_text(strip=True)
            if ('nearby' in text.lower() or 'pick' in text.lower()) and len(text) < 100:
                relevant_spans.append((span, text))
        
        if relevant_spans:
            print(f"\n✅ Found {len(relevant_spans)} relevant <span> elements:")
            for span, text in relevant_spans[:15]:
                classes = span.get('class', [])
                print(f"  • <span class='{' '.join(classes) if classes else 'none'}'>{text}</span>")
        else:
            print("\n❌ No relevant <span> elements found")
        
        # Strategy 5: Check if there's a "Nearby" filter/tab visible
        print("\n" + "="*80)
        print("STRATEGY 5: Look for 'Nearby' filter/tab")
        print("="*80)
        
        try:
            nearby_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Nearby')]")
            if nearby_buttons:
                print(f"\n✅ Found {len(nearby_buttons)} elements with 'Nearby' text:")
                for button in nearby_buttons[:5]:
                    print(f"  • Tag: {button.tag_name}, Text: {button.text}, Displayed: {button.is_displayed()}")
            else:
                print("\n❌ No 'Nearby' button/filter found")
        except Exception as e:
            print(f"\n⚠️  Error looking for Nearby button: {e}")
        
        # Final summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        total_found = len(nearby_matches) + len(pickup_matches)
        
        if total_found > 0:
            print(f"\n✅ SUCCESS! Found {total_found} availability indicators")
            print(f"   • {len(nearby_matches)} distance indicators")
            print(f"   • {len(pickup_matches)} pickup indicators")
        else:
            print("\n❌ FAILED! No availability indicators found")
            print("\n💡 Debugging info:")
            print(f"   • Page title: {soup.title.string if soup.title else 'None'}")
            print(f"   • Page size: {len(html):,} bytes")
            print(f"   • Total spans: {len(all_spans)}")
            print(f"   • Check the screenshot and HTML file for manual inspection")
        
        input("\nPress Enter to close browser...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    test_nearby_data()

