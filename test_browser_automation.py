#!/usr/bin/env python3
"""
Browser Automation Test for Low Cost Groceries
Tests the complete user flow through the Vercel frontend
"""

import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
VERCEL_URL = "https://lowcost-groceries-frontend.vercel.app"
TEST_ZIP_CODES = ["60614", "90210", "70072"]

# Same 20 carts as the original test (200 products total)
PRODUCT_CARTS = [
    # Cart 1: Fresh Produce
    ["Bananas", "Apples", "Oranges", "Grapes", "Strawberries", "Blueberries", "Lemons", "Limes", "Russet potatoes", "Sweet potatoes"],
    
    # Cart 2: Fresh Produce 2
    ["Yellow onions", "Garlic", "Tomatoes", "Romaine lettuce", "Iceberg lettuce", "Spinach", "Broccoli", "Carrots", "Bell peppers", "Cucumbers"],
    
    # Cart 3: Dairy
    ["Whole milk", "2% milk", "Skim milk", "Half & half", "Heavy cream", "Salted butter", "Unsalted butter", "American cheese slices", "Cheddar cheese", "Mozzarella"],
    
    # Cart 4: More Dairy
    ["Yogurt", "Greek yogurt", "Cottage cheese", "Sour cream", "Cream cheese", "String cheese", "Eggs dozen large", "Almond milk", "Oat milk", "Shredded Mexican cheese"],
    
    # Cart 5: Meat & Seafood
    ["Ground beef", "Boneless skinless chicken breasts", "Chicken thighs", "Whole chicken", "Pork chops", "Bacon", "Breakfast sausage links", "Deli turkey breast", "Deli ham", "Hot dogs"],
    
    # Cart 6: More Meat
    ["Italian sausage", "Ground pork", "Pork tenderloin", "Ribeye steak", "Sirloin steak", "Ground turkey", "Frozen shrimp", "Salmon fillets", "Tilapia fillets", "Frozen meatballs"],
    
    # Cart 7: Bread & Bakery
    ["White sandwich bread", "Wheat bread", "Hamburger buns", "Hot dog buns", "Flour tortillas", "Corn tortillas", "Plain bagels", "English muffins", "Dinner rolls", "Croissants"],
    
    # Cart 8: More Bakery
    ["Pita bread", "Garlic bread frozen", "Sweet rolls", "Donuts", "Sub rolls", "Gluten-free bread", "Cake mix", "Brownie mix", "Cookie dough", "Pie crust"],
    
    # Cart 9: Pantry Staples
    ["All-purpose flour", "Granulated sugar", "Brown sugar", "Powdered sugar", "Baking soda", "Baking powder", "Table salt", "Kosher salt", "Black pepper", "Olive oil"],
    
    # Cart 10: More Pantry
    ["Vegetable oil", "White rice", "Brown rice", "Spaghetti", "Elbow macaroni", "Dry black beans", "Dry pinto beans", "Breadcrumbs", "Chicken bouillon", "Cornstarch"],
]

class BrowserTest:
    def __init__(self, headless=False):
        """Initialize the browser"""
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver"""
        logger.info("🌐 Setting up Chrome browser...")
        
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)
        logger.info("✅ Browser ready")
        
    def open_site(self):
        """Open the Vercel site"""
        logger.info(f"🔗 Opening {VERCEL_URL}...")
        self.driver.get(VERCEL_URL)
        time.sleep(2)
        logger.info(f"✅ Site loaded: {self.driver.title}")
        
    def add_item_with_ai(self, item_name):
        """Add an item using AI suggestions"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📝 Adding item: {item_name}")
        logger.info(f"{'='*60}")
        
        try:
            # Find the input field
            input_field = self.driver.find_element(By.ID, "itemInput")
            input_field.clear()
            input_field.send_keys(item_name)
            logger.info(f"⌨️  Typed: {item_name}")
            
            # Click "Get AI Suggestions" button
            logger.info("🤖 Clicking 'Get AI Suggestions' button...")
            ai_button = self.driver.find_element(By.ID, "addManualBtn")
            ai_button.click()
            time.sleep(1)
            
            # Wait for AI suggestion cards to appear
            logger.info("⏳ Waiting for AI suggestion cards...")
            wait = WebDriverWait(self.driver, 30)
            suggestion_cards = wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".suggestion-card"))
            )
            
            if suggestion_cards and len(suggestion_cards) >= 2:
                logger.info(f"✅ Found {len(suggestion_cards)} AI suggestions!")
                
                # Get the second card (first is "Use As-Is", second is AI recommendation)
                ai_card = suggestion_cards[1]
                suggested_text = ai_card.find_element(By.CSS_SELECTOR, ".suggestion-name").text
                logger.info(f"💡 AI suggested: {suggested_text}")
                
                # Click the AI suggestion
                ai_card.click()
                logger.info(f"✅ Added to cart: {suggested_text}")
                time.sleep(1)
                return True
            elif suggestion_cards:
                # Fallback if only one card
                logger.warning("⚠️  Only one suggestion, clicking it")
                suggestion_cards[0].click()
                time.sleep(1)
                return True
            else:
                logger.error("❌ No suggestion cards found")
                return False
                
        except TimeoutException:
            logger.error(f"❌ Timeout waiting for AI suggestions for '{item_name}'")
            return False
        except Exception as e:
            logger.error(f"❌ Error adding item: {e}")
            return False
    
    def get_cart_items(self):
        """Get the current items in the cart"""
        try:
            cart_items = self.driver.find_elements(By.CSS_SELECTOR, "#cartItems li")
            items = [item.text for item in cart_items]
            return items
        except:
            return []
    
    def submit_cart(self, zipcode):
        """Submit the cart with a ZIP code"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📤 Submitting cart with ZIP: {zipcode}")
        logger.info(f"{'='*60}")
        
        try:
            # Enter ZIP code
            zip_input = self.driver.find_element(By.ID, "zipInput")
            zip_input.clear()
            zip_input.send_keys(zipcode)
            logger.info(f"📍 Entered ZIP: {zipcode}")
            
            # Click submit button
            submit_button = self.driver.find_element(By.ID, "findPricesBtn")
            submit_button.click()
            logger.info("🔍 Clicked 'Find Lowest Prices'")
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error submitting cart: {e}")
            return False
    
    def wait_for_results(self, timeout=120):
        """Wait for results to appear"""
        logger.info(f"\n{'='*60}")
        logger.info(f"⏳ Waiting for results (max {timeout}s)...")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Wait for results section (step3) to appear and have result cards
            wait = WebDriverWait(self.driver, timeout)
            
            # Wait for at least one result card to appear
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".result-card"))
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Results appeared after {elapsed:.1f}s")
            
            # Give a moment for all results to render
            time.sleep(2)
            
            return True
            
        except TimeoutException:
            elapsed = time.time() - start_time
            logger.error(f"❌ Timeout waiting for results after {elapsed:.1f}s")
            return False
        except Exception as e:
            logger.error(f"❌ Error waiting for results: {e}")
            return False
    
    def get_results_summary(self):
        """Get a summary of the results"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RESULTS SUMMARY")
        logger.info(f"{'='*60}")
        
        try:
            result_cards = self.driver.find_elements(By.CSS_SELECTOR, ".result-card")
            
            if not result_cards:
                logger.warning("⚠️  No results found")
                return
            
            logger.info(f"Found {len(result_cards)} items with prices:")
            
            for card in result_cards:
                try:
                    item_name = card.find_element(By.CSS_SELECTOR, ".result-item-name").text
                    # Get first product row (best price)
                    first_product = card.find_element(By.CSS_SELECTOR, ".product-row")
                    price = first_product.find_element(By.CSS_SELECTOR, ".product-price").text
                    merchant = first_product.find_element(By.CSS_SELECTOR, ".product-merchant").text
                    logger.info(f"  ✅ {item_name}: {price} at {merchant}")
                except Exception as e:
                    logger.warning(f"  ⚠️  Could not parse result card: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error getting results: {e}")
    
    def take_screenshot(self, filename):
        """Take a screenshot"""
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save screenshot: {e}")
    
    def cleanup(self):
        """Close the browser"""
        if self.driver:
            logger.info("🧹 Closing browser...")
            self.driver.quit()
            logger.info("✅ Browser closed")


def run_test(headless=False):
    """Run the complete browser automation test"""
    test = BrowserTest(headless=headless)
    
    try:
        logger.info("="*80)
        logger.info("🚀 STARTING BROWSER AUTOMATION TEST: 100 Products, 10 Carts, 3 ZIP Codes")
        logger.info("="*80)
        overall_start = time.time()
        
        # Setup browser once
        test.setup_driver()
        
        cart_num = 1
        total_success = 0
        total_failed = 0
        
        for cart_items in PRODUCT_CARTS:
            for zipcode in TEST_ZIP_CODES:
                logger.info(f"\n{'='*80}")
                logger.info(f"🛒 CART #{cart_num}: {len(cart_items)} items in ZIP {zipcode}")
                logger.info(f"{'='*80}")
                
                cart_start = time.time()
                
                # Open site fresh for each cart
                test.open_site()
                
                # Add items with AI
                success_count = 0
                for item in cart_items:
                    if test.add_item_with_ai(item):
                        success_count += 1
                    time.sleep(0.5)  # Shorter delay
                
                logger.info(f"\n📊 Added {success_count}/{len(cart_items)} items")
                
                # Click Continue button
                try:
                    continue_button = test.driver.find_element(By.ID, "continueBtn")
                    continue_button.click()
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"❌ Failed to continue: {e}")
                    test.take_screenshot(f"error_cart_{cart_num}.png")
                    total_failed += 1
                    cart_num += 1
                    continue
                
                # Submit cart
                if not test.submit_cart(zipcode):
                    logger.error("❌ Failed to submit cart")
                    test.take_screenshot(f"error_submit_{cart_num}.png")
                    total_failed += 1
                    cart_num += 1
                    continue
                
                # Wait for results
                if not test.wait_for_results(timeout=120):
                    logger.error("❌ Failed to get results")
                    test.take_screenshot(f"error_results_{cart_num}.png")
                    total_failed += 1
                    cart_num += 1
                    continue
                
                # Show results
                test.get_results_summary()
                
                cart_elapsed = time.time() - cart_start
                logger.info(f"\n✅ Cart #{cart_num} completed in {cart_elapsed:.1f}s")
                total_success += 1
                cart_num += 1
                
                # Small delay between carts
                time.sleep(2)
        
        overall_elapsed = time.time() - overall_start
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 FINAL RESULTS")
        logger.info(f"{'='*80}")
        logger.info(f"Total Carts: {cart_num - 1}")
        logger.info(f"✅ Successful: {total_success}")
        logger.info(f"❌ Failed: {total_failed}")
        logger.info(f"⏱️  Total Time: {overall_elapsed:.1f}s")
        logger.info(f"{'='*80}")
        
        test.take_screenshot("final_results.png")
        
        return total_failed == 0
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        test.take_screenshot("error_exception.png")
        return False
        
    finally:
        test.cleanup()


if __name__ == "__main__":
    import sys
    
    # Check if headless mode requested
    headless = "--headless" in sys.argv
    
    if headless:
        logger.info("Running in HEADLESS mode (no visible browser)")
    else:
        logger.info("Running with VISIBLE browser (you can watch it work)")
    
    success = run_test(headless=headless)
    sys.exit(0 if success else 1)

