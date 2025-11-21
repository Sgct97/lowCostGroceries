#!/usr/bin/env python3
"""
Production Google Shopping Scraper - UC-Based
Uses Undetected ChromeDriver with all proven optimizations

PROVEN SOLUTIONS:
1. Location override with ZIP code in URL
2. NO headless mode (use Xvfb on servers)
3. Fresh browser per request to avoid bot detection
4. Correct URL pattern: q=milk+near+zip+ZIP+nearby&udm=28&shopmd=4
5. Parse products from aria-labels
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from bs4 import BeautifulSoup
import urllib.parse
import re
import logging
from typing import List, Dict, Optional
from multiprocessing import Process, Queue
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductParser:
    """Parses product data from Google Shopping HTML"""
    
    @staticmethod
    def extract_products_from_html(html_content: str) -> List[Dict]:
        """
        Extract products using the PROVEN method from our working tests
        Uses CSS selectors to find product containers and extract data
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # Find all product containers with aria-label (these are product cards)
        product_elements = soup.find_all(attrs={'aria-label': True})
        
        for element in product_elements:
            aria_label = element.get('aria-label', '')
            
            # Skip if not a product (filter out navigation, filters, etc.)
            if not aria_label or len(aria_label) < 10:
                continue
            if 'filter' in aria_label.lower() or 'button' in aria_label.lower():
                continue
            if not '$' in aria_label:
                continue
            
            try:
                # Parse the aria-label which contains structured product info
                # Example: "Whole Milk. Current Price: $3.69. Walmart. Rated 4.5 out of 5."
                
                # Extract price FIRST before splitting (to preserve $X.XX format)
                price = None
                price_match = re.search(r'\$(\d+\.\d+|\d+)', aria_label)
                if price_match:
                    price = float(price_match.group(1))
                
                # NOW split by periods
                parts = aria_label.split('.')
                
                # Product name (first part)
                product_name = parts[0].strip() if len(parts) > 0 else None
                
                # Merchant - usually the part after price
                merchant = None
                for i, part in enumerate(parts):
                    if '$' in part and i + 1 < len(parts):
                        candidate = parts[i + 1].strip()
                        # Make sure it's not a rating or review
                        if candidate and 'Rated' not in candidate and 'review' not in candidate and len(candidate) > 0:
                            merchant = candidate
                            break
                
                # Rating
                rating = None
                rating_match = re.search(r'Rated (\d+\.?\d*) out of', aria_label)
                if rating_match:
                    rating = float(rating_match.group(1))
                
                # Review count
                review_count = None
                review_match = re.search(r'([\d.]+)([KM])?\s*reviews?', aria_label, re.IGNORECASE)
                if review_match:
                    num = float(review_match.group(1))
                    multiplier = review_match.group(2)
                    if multiplier == 'K':
                        num *= 1000
                    elif multiplier == 'M':
                        num *= 1000000
                    review_count = int(num)
                
                # Only add if we have minimum data and merchant looks valid
                if product_name and price and merchant and len(merchant) > 1:
                    products.append({
                        'name': product_name,
                        'price': price,
                        'merchant': merchant,
                        'rating': rating,
                        'review_count': review_count
                    })
            
            except Exception as e:
                logger.debug(f"Error parsing product: {e}")
                continue
        
        return products
    
    @staticmethod
    def get_merchants_from_html(html_content: str) -> List[str]:
        """Extract all merchant names from HTML (for debugging/validation)"""
        soup = BeautifulSoup(html_content, 'html.parser')
        merchant_elements = soup.select('span.WJMUdc.rw5ecc')
        if not merchant_elements:
            merchant_elements = soup.select('span.WJMUdc')
        merchants = [m.get_text(strip=True) for m in merchant_elements]
        return list(set(merchants))


class UCGoogleShoppingScraper:
    """
    Production Google Shopping scraper using Undetected ChromeDriver
    
    CRITICAL SETUP:
    - NO headless mode (use Xvfb on servers)
    - Fresh browser for each search to avoid bot detection
    - Correct URL pattern with ZIP code
    """
    
    def __init__(self, use_xvfb: bool = False):
        """
        Initialize scraper
        
        Args:
            use_xvfb: If True, assumes running on server with Xvfb (headless display)
        """
        self.use_xvfb = use_xvfb
        self.parser = ProductParser()
        logger.info(f"UCGoogleShoppingScraper initialized (xvfb={use_xvfb})")
    
    def _setup_driver(self) -> uc.Chrome:
        """
        Setup UC Chrome driver with proven configuration
        
        CRITICAL: NO --headless flag! Use Xvfb instead on servers.
        """
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--remote-debugging-port=0")  # Let Chrome pick random port
        
        # DO NOT USE --headless=new (causes CAPTCHA)
        # If on server, run with: xvfb-run -a python3 script.py
        
        return uc.Chrome(
            options=options, 
            use_subprocess=False,
            driver_executable_path='/usr/bin/chromedriver',
            browser_executable_path='/usr/bin/google-chrome'
        )
    
    def _build_search_url(self, search_term: str, zip_code: str) -> str:
        """
        Build the proven URL pattern for location-specific results
        
        Pattern: https://www.google.com/search?q={term}+near+zip+{zip}+nearby&udm=28&shopmd=4
        """
        query = f"{search_term} near zip {zip_code} nearby"
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&udm=28&shopmd=4"
        logger.info(f"🔗 Search URL: {url}")
        return url
    
    def _check_for_captcha(self, html: str) -> bool:
        """Check if page is a CAPTCHA challenge"""
        return 'detected unusual traffic' in html or 'recaptcha' in html.lower()
    
    def _extract_products(self, driver, prioritize_nearby: bool = True) -> List[Dict]:
        """Extract products from current page using PROVEN Selenium method"""
        html = driver.page_source
        
        # Check for CAPTCHA
        if self._check_for_captcha(html):
            logger.error("CAPTCHA detected!")
            return []
        
        # Use Selenium to get merchants (PROVEN method from test_nearby_url_pattern.py)
        from selenium.webdriver.common.by import By
        
        try:
            # Get ALL merchant elements using CSS selector (PROVEN method from working script)
            merchant_elements = driver.find_elements(By.CSS_SELECTOR, "span.WJMUdc.rw5ecc")
            merchants = [m.text for m in merchant_elements if m.text]
            
            logger.info(f"Found {len(merchants)} merchant elements")
            
            # Now extract products from aria-labels and match with merchants
            soup = BeautifulSoup(html, 'html.parser')
            products = []
            
            # If user wants to prioritize nearby, try to find "In stores nearby" section
            if prioritize_nearby:
                nearby_section = soup.find('div', {'jsname': 'EvNWZc'})
                if nearby_section:
                    logger.info("✓ Found 'In stores nearby' section, filtering to local stores only")
                    product_elements = nearby_section.find_all(attrs={'aria-label': True})
                else:
                    logger.info("✗ 'In stores nearby' section not found, falling back to all products")
                    product_elements = soup.find_all(attrs={'aria-label': True})
            else:
                logger.info("ℹ️ Prioritize nearby = OFF, using all products for best prices")
                product_elements = soup.find_all(attrs={'aria-label': True})
            
            merchant_idx = 0
            for element in product_elements:
                aria_label = element.get('aria-label', '')
                
                # Skip non-products
                if not aria_label or len(aria_label) < 10:
                    continue
                if 'filter' in aria_label.lower() or 'button' in aria_label.lower():
                    continue
                if not '$' in aria_label:
                    continue
                
                # Parse product data
                try:
                    # Extract price FIRST before splitting (preserves $X.XX format)
                    price = None
                    price_match = re.search(r'\$(\d+\.\d+|\d+)', aria_label)
                    if price_match:
                        price = float(price_match.group(1))
                    
                    # NOW split by periods
                    parts = aria_label.split('.')
                    product_name = parts[0].strip() if len(parts) > 0 else None
                    
                    # Use merchant from Selenium extraction
                    merchant = merchants[merchant_idx] if merchant_idx < len(merchants) else None
                    merchant_idx += 1
                    
                    # Rating
                    rating = None
                    rating_match = re.search(r'Rated (\d+\.?\d*) out of', aria_label)
                    if rating_match:
                        rating = float(rating_match.group(1))
                    
                    # Review count
                    review_count = None
                    review_match = re.search(r'([\d.]+)([KM])?\s*reviews?', aria_label, re.IGNORECASE)
                    if review_match:
                        num = float(review_match.group(1))
                        multiplier = review_match.group(2)
                        if multiplier == 'K':
                            num *= 1000
                        elif multiplier == 'M':
                            num *= 1000000
                        review_count = int(num)
                    
                    # Only add if we have minimum data
                    if product_name and price and merchant:
                        products.append({
                            'name': product_name,
                            'price': price,
                            'merchant': merchant,
                            'rating': rating,
                            'review_count': review_count
                        })
                
                except Exception as e:
                    logger.debug(f"Error parsing product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error extracting products: {e}")
            return []
    
    def search(
        self, 
        search_term: str, 
        zip_code: str, 
        max_products: int = 50,
        wait_time: int = None,
        driver=None,
        close_driver: bool = True,
        prioritize_nearby: bool = True
    ) -> List[Dict]:
        """
        Search Google Shopping for a product in a specific location
        
        Args:
            search_term: Product to search (e.g., "milk", "eggs")
            zip_code: User's ZIP code for location-specific results
            max_products: Maximum number of products to return
            wait_time: Seconds to wait for page load (auto: 5s fresh, 2.5s persistent)
            driver: Optional existing driver to reuse (FAST!)
            close_driver: If True, close driver after search (default)
        
        Returns:
            List of product dictionaries with name, price, merchant, etc.
        """
        logger.info(f"Searching '{search_term}' in ZIP {zip_code}")
        
        driver_provided = driver is not None
        
        try:
            # Use provided driver or create fresh one
            if not driver:
                driver = self._setup_driver()
                # Auto wait time based on browser type
                if wait_time is None:
                    wait_time = 1  # Fresh browser first load (proven to work!)
            else:
                # Persistent browser loads faster
                if wait_time is None:
                    wait_time = 0.5  # Persistent browser (proven from earlier tests!)
            
            # Build URL
            url = self._build_search_url(search_term, zip_code)
            logger.debug(f"Loading: {url}")
            
            # Load page
            driver.get(url)
            time.sleep(wait_time)
            
            # Scroll to load lazy-loaded products in "In stores nearby"
            logger.info("Scrolling to load all products...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            
            # Save HTML for debugging
            import os
            os.makedirs('/tmp/scraper_debug', exist_ok=True)
            safe_term = search_term.replace(' ', '_').replace(',', '')[:30]
            debug_path = f'/tmp/scraper_debug/{safe_term}_{zip_code}.html'
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"💾 Saved HTML: {debug_path}")
            
            # Extract products
            products = self._extract_products(driver, prioritize_nearby)
            
            logger.info(f"Found {len(products)} products")
            
            # Limit results
            return products[:max_products]
            
        except TimeoutException:
            logger.error(f"Timeout loading page for '{search_term}'")
            return []
        except NoSuchElementException as e:
            logger.error(f"Element not found: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching '{search_term}': {e}")
            return []
        finally:
            # Only close if we created it AND close_driver=True
            if driver and not driver_provided and close_driver:
                driver.quit()
    
    def search_multiple_sequential(
        self,
        search_terms: List[str],
        zip_code: str,
        max_products_per_search: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Search multiple products SEQUENTIALLY using ONE persistent browser
        
        PROVEN TIMINGS (from earlier tests):
        - First search: ~3-4 seconds (browser startup + 1s wait)
        - Subsequent: ~1.5 seconds each (page navigation + 0.5s wait)
        - 5 items: ~9-10 seconds total!
        
        Args:
            search_terms: List of products to search
            zip_code: User's ZIP code
            max_products_per_search: Max products per search
        
        Returns:
            Dict mapping search_term -> list of products
        """
        logger.info(f"Sequential search: {len(search_terms)} items in ZIP {zip_code}")
        
        driver = None
        results = {}
        
        try:
            # Create ONE browser for all searches
            driver = self._setup_driver()
            
            for i, term in enumerate(search_terms):
                # Use PROVEN wait times from earlier tests
                # First search: 1s, subsequent: 0.5s (worked perfectly!)
                wait_time = 1 if i == 0 else 0.5
                
                products = self.search(
                    term, 
                    zip_code, 
                    max_products_per_search,
                    wait_time=wait_time,  # PROVEN: 1s first, 0.5s subsequent
                    driver=driver,  # REUSE the browser!
                    close_driver=False  # Don't close it yet
                )
                results[term] = products
            
            return results
            
        finally:
            if driver:
                driver.quit()
    
    def search_multiple_parallel(
        self,
        search_terms: List[str],
        zip_code: str,
        max_products_per_search: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Search multiple products in parallel using multiprocessing
        
        PROVEN: 2-3 parallel browsers per machine works reliably
        
        Args:
            search_terms: List of products to search
            zip_code: User's ZIP code
            max_products_per_search: Max products per search
        
        Returns:
            Dict mapping search_term -> list of products
        """
        logger.info(f"Parallel search: {len(search_terms)} items in ZIP {zip_code}")
        
        def worker(term: str, zip_code: str, result_queue: Queue):
            """Worker process for parallel search"""
            try:
                scraper = UCGoogleShoppingScraper(use_xvfb=self.use_xvfb)
                products = scraper.search(term, zip_code, max_products_per_search)
                result_queue.put((term, products))
            except Exception as e:
                logger.error(f"Worker error for '{term}': {e}")
                result_queue.put((term, []))
        
        # Create result queue
        result_queue = Queue()
        
        # Launch workers
        processes = []
        for term in search_terms:
            p = Process(target=worker, args=(term, zip_code, result_queue))
            p.start()
            processes.append(p)
            time.sleep(2)  # Stagger launches
        
        # Wait for all to complete
        for p in processes:
            p.join()
        
        # Collect results
        results = {}
        while not result_queue.empty():
            term, products = result_queue.get()
            results[term] = products
        
        logger.info(f"Parallel search complete: {len(results)} items")
        return results


# ============================================================================
# PRODUCTION API
# ============================================================================

def search_products(
    search_terms: List[str],
    zip_code: str,
    max_products_per_item: int = 20,
    use_parallel: bool = True
) -> Dict[str, List[Dict]]:
    """
    Production API for searching Google Shopping
    
    PERFORMANCE:
    - Sequential (1 browser, reused): ~8s first + 3s per item = ~17s for 4 items
    - Parallel (2 browsers): ~8s total for 2 items, ~12s for 4 items
    
    Args:
        search_terms: List of products (e.g., ["milk", "eggs", "bread"])
        zip_code: User's ZIP code for location-specific results
        max_products_per_item: Max products to return per search term
        use_parallel: If True and >3 items, use parallel (default: True)
    
    Returns:
        Dict mapping search_term -> list of products
        
    Example:
        results = search_products(["milk", "eggs"], "10001", max_products_per_item=10)
        # returns: {
        #   "milk": [{"name": "Whole Milk", "price": 3.69, "merchant": "Walmart"}, ...],
        #   "eggs": [{"name": "Large Eggs", "price": 2.99, "merchant": "Target"}, ...]
        # }
    """
    # Determine if running on server (check for DISPLAY env var)
    use_xvfb = os.environ.get('DISPLAY') is None or os.environ.get('XVFB') == '1'
    
    scraper = UCGoogleShoppingScraper(use_xvfb=use_xvfb)
    
    # Use parallel only for 4+ items (for 1-3 items, sequential is faster)
    if use_parallel and len(search_terms) >= 4:
        # Parallel search (2-3 browsers)
        return scraper.search_multiple_parallel(
            search_terms, 
            zip_code, 
            max_products_per_item
        )
    else:
        # Sequential search with persistent browser (FASTER for 1-3 items!)
        return scraper.search_multiple_sequential(
            search_terms,
            zip_code,
            max_products_per_item
        )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_single_search():
    """Example: Search one product"""
    print("="*80)
    print("EXAMPLE 1: Single Product Search")
    print("="*80)
    
    scraper = UCGoogleShoppingScraper()
    products = scraper.search("milk", "10001", max_products=10)
    
    print(f"\n✅ Found {len(products)} products:")
    for i, p in enumerate(products, 1):
        print(f"{i}. {p['name']} - ${p['price']} @ {p['merchant']}")


def example_parallel_search():
    """Example: Search multiple products in parallel"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Parallel Multi-Product Search")
    print("="*80)
    
    results = search_products(
        search_terms=["milk", "eggs", "bread"],
        zip_code="10001",
        max_products_per_item=5,
        use_parallel=True
    )
    
    print(f"\n✅ Found results for {len(results)} items:")
    for term, products in results.items():
        print(f"\n📦 {term.upper()} ({len(products)} products):")
        for i, p in enumerate(products[:3], 1):
            print(f"  {i}. {p['name']} - ${p['price']} @ {p['merchant']}")


if __name__ == "__main__":
    # Run examples
    example_single_search()
    # example_parallel_search()  # Uncomment to test parallel

