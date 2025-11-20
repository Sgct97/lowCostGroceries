#!/usr/bin/env python3
"""
Test clicking the 'Nearby' filter to get local pickup and distance data
"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from bs4 import BeautifulSoup

def test_nearby_filter(zip_code="33773", search_term="milk"):
    """Test the Nearby filter to get local pickup data"""
    print(f"\n{'='*80}")
    print(f"Testing Nearby Filter for ZIP {zip_code}")
    print(f"{'='*80}")
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = uc.Chrome(options=options, use_subprocess=False)
    
    try:
        # Use the nearby URL pattern
        query = f"{search_term} near zip {zip_code} nearby"
        encoded_query = query.replace(" ", "+")
        url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4"
        
        print(f"\n✓ Loading: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Try to click the "Nearby" filter/tab if it exists
        try:
            print("\n✓ Looking for 'Nearby' filter tab...")
            # Try multiple selectors for the Nearby button
            nearby_selectors = [
                "//div[@role='button' and contains(text(), 'Nearby')]",
                "//span[contains(text(), 'Nearby')]/ancestor::div[@role='button']",
                "//button[contains(text(), 'Nearby')]",
            ]
            
            nearby_clicked = False
            for selector in nearby_selectors:
                try:
                    nearby_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    nearby_button.click()
                    print(f"✓ Clicked 'Nearby' filter!")
                    nearby_clicked = True
                    time.sleep(3)  # Wait for filter to apply
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not nearby_clicked:
                print("⚠️  Could not find/click 'Nearby' filter - may already be active")
                
        except Exception as e:
            print(f"⚠️  Error clicking Nearby filter: {e}")
        
        # Now parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for "Nearby, X mi" badges
        print("\n" + "="*80)
        print("SEARCHING FOR DISTANCE INDICATORS")
        print("="*80)
        
        # Search for text containing "Nearby" and "mi"
        distance_elements = soup.find_all(text=lambda t: t and 'Nearby' in str(t) and 'mi' in str(t))
        print(f"\n✓ Found {len(distance_elements)} elements with 'Nearby' + 'mi':")
        
        distances_found = set()
        for elem in distance_elements:
            text = elem.strip()
            if len(text) < 50:  # Keep it short
                distances_found.add(text)
        
        for dist in sorted(distances_found):
            print(f"  • {dist}")
        
        # Look for "Pick up today" badges
        print("\n" + "="*80)
        print("SEARCHING FOR PICKUP INDICATORS")
        print("="*80)
        
        pickup_elements = soup.find_all(text=lambda t: t and 'Pick up' in str(t))
        print(f"\n✓ Found {len(pickup_elements)} elements with 'Pick up':")
        
        pickups_found = set()
        for elem in pickup_elements:
            text = elem.strip()
            if len(text) < 50:
                pickups_found.add(text)
        
        for pickup in sorted(pickups_found):
            print(f"  • {pickup}")
        
        # Now find products WITH these badges
        print("\n" + "="*80)
        print("EXTRACTING PRODUCTS WITH LOCAL AVAILABILITY")
        print("="*80)
        
        # Look for product containers with aria-label (these contain full product info)
        products_with_availability = []
        product_elements = soup.find_all(attrs={'aria-label': lambda x: x and ('Nearby' in x or 'Pick up' in x)})
        
        print(f"\n✓ Found {len(product_elements)} products with local availability:")
        
        for i, product in enumerate(product_elements[:10], 1):
            aria_label = product.get('aria-label', '')
            
            # Extract product name (usually first part before period)
            parts = aria_label.split('.')
            product_name = parts[0].strip() if parts else 'Unknown'
            
            # Extract price
            price = 'N/A'
            for part in parts:
                if 'Current Price:' in part or '$' in part:
                    price_match = part.strip()
                    if '$' in price_match:
                        price = price_match.split('$')[1].split()[0] if '$' in price_match else 'N/A'
                        price = f"${price}"
                        break
            
            # Extract merchant
            merchant = 'Unknown'
            for part in parts:
                if 'Walmart' in part or 'Target' in part or 'Publix' in part or 'Instacart' in part:
                    merchant = part.strip().rstrip('.')
                    break
            
            # Extract availability info
            availability = []
            for part in parts:
                if 'Nearby' in part:
                    availability.append(part.strip())
                if 'Pick up' in part:
                    availability.append(part.strip())
            
            print(f"\n{i}. {product_name}")
            print(f"   Price: {price}")
            print(f"   Merchant: {merchant}")
            if availability:
                print(f"   Availability: {', '.join(availability)}")
        
        # Save HTML
        html_filename = f"nearby_filter_{zip_code}.html"
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"\n💾 Saved HTML to: {html_filename}")
        
        if distances_found or pickups_found:
            print("\n" + "="*80)
            print("✅ SUCCESS! Found local availability data:")
            print(f"   • {len(distances_found)} unique distance indicators")
            print(f"   • {len(pickups_found)} unique pickup indicators")
            print("="*80)
            return True
        else:
            print("\n" + "="*80)
            print("❌ FAILED! No local availability data found")
            print("="*80)
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test Florida ZIP (where we know Publix exists)
    test_nearby_filter("33773", "milk")

