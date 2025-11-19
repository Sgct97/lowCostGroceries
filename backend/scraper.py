"""
Google Shopping Scraper with Session-Based Architecture

Uses CallbackSessionManager to get valid callback URLs, then makes
fast requests with curl_cffi. No browser automation in the hot path!

Architecture:
- TokenService (background): Creates callback sessions with Playwright
- SessionManager (pool): Manages session health and pool
- Scraper (this): Uses sessions for fast requests-only scraping
"""

from curl_cffi import requests  # Use curl_cffi instead of requests
from bs4 import BeautifulSoup
import re
import json
import logging
from typing import List, Dict, Optional
from proxy_manager import ProxyPool, Proxy
from session_manager import get_session_manager
from callback_session import CallbackSession
import time
import random


logger = logging.getLogger(__name__)


class Product:
    """Product data structure"""
    
    def __init__(self, data: Dict):
        self.title = data.get('title')
        self.price = data.get('price')
        self.original_price = data.get('original_price')
        self.merchant = data.get('merchant')
        self.rating = data.get('rating')
        self.review_count = data.get('review_count')
        self.image_url = data.get('image_url')
        self.product_id = data.get('product_id')
    
    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'price': self.price,
            'original_price': self.original_price,
            'merchant': self.merchant,
            'rating': self.rating,
            'review_count': self.review_count,
            'image_url': self.image_url,
            'product_id': self.product_id
        }


class GoogleShoppingScraper:
    """
    Production-ready Google Shopping scraper with:
    - ISP proxy rotation
    - Automatic retry on failure
    - Rate limiting
    - Error handling
    """
    
    def __init__(self, proxy_pool: Optional[ProxyPool] = None, region: str = "US-West"):
        self.proxy_pool = proxy_pool
        self.region = region
        self.session_manager = get_session_manager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        
        logger.info(f"GoogleShoppingScraper initialized for region={region}")
    
    def _make_request(
        self, 
        url: str, 
        max_retries: int = 3,
        timeout: int = 15
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with proxy rotation and retry logic
        
        Args:
            url: URL to request
            max_retries: Max number of retry attempts
            timeout: Request timeout in seconds
            
        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(max_retries):
            proxy = None
            proxies_dict = None
            
            # Get proxy if pool exists
            if self.proxy_pool:
                proxy = self.proxy_pool.get_next_proxy()
                if not proxy:
                    print(f"⚠️  No proxies available, attempt {attempt + 1}/{max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                proxies_dict = proxy.dict
            
            try:
                # Add random delay to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(1, 3)
                    time.sleep(delay)
                
                response = self.session.get(
                    url,
                    proxies=proxies_dict,
                    timeout=timeout,
                    allow_redirects=True,
                    impersonate="chrome120"  # CRITICAL: Browser impersonation
                )
                
                # Check if blocked (CAPTCHA page)
                if 'captcha' in response.text.lower() or response.status_code == 403:
                    if proxy and self.proxy_pool:
                        self.proxy_pool.report_failure(proxy, is_blocked=True)
                    print(f"🚫 Blocked (attempt {attempt + 1}/{max_retries})")
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.ProxyError as e:
                if proxy and self.proxy_pool:
                    self.proxy_pool.report_failure(proxy)
                print(f"❌ Proxy error (attempt {attempt + 1}/{max_retries}): {e}")
                
            except requests.exceptions.Timeout as e:
                if proxy and self.proxy_pool:
                    self.proxy_pool.report_failure(proxy)
                print(f"⏱️  Timeout (attempt {attempt + 1}/{max_retries})")
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Request error (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)
        
        return None
    
    def _parse_product(self, container) -> Optional[Dict]:
        """Parse a single product from HTML"""
        try:
            soup = BeautifulSoup(str(container), 'html.parser')
            
            # Title
            title_elem = soup.find('div', class_='gkQHve')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Price
            price = None
            price_elem = soup.find('span', class_='lmQWe')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if match:
                    price = float(match.group(1).replace(',', ''))
            
            # Original price
            original_price = None
            was_price = soup.find('span', class_='DoCHT')
            if was_price:
                price_text = was_price.get_text(strip=True)
                match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if match:
                    original_price = float(match.group(1).replace(',', ''))
            
            # Merchant
            merchant_elem = soup.find('span', class_='WJMUdc')
            merchant = merchant_elem.get_text(strip=True) if merchant_elem else None
            
            # Rating
            rating = None
            rating_elem = soup.find('span', class_='yi40Hd')
            if rating_elem:
                try:
                    rating = float(rating_elem.get_text(strip=True))
                except ValueError:
                    pass
            
            # Reviews
            reviews = None
            reviews_elem = soup.find('span', class_='RDApEe')
            if reviews_elem:
                text = reviews_elem.get_text(strip=True)
                match = re.search(r'\(([0-9.]+)([KM])?\)', text)
                if match:
                    num = float(match.group(1))
                    multiplier = match.group(2)
                    if multiplier == 'K':
                        num *= 1000
                    elif multiplier == 'M':
                        num *= 1000000
                    reviews = int(num)
            
            # Image
            image_url = None
            img = soup.find('img', class_='VeBrne')
            if img:
                image_url = img.get('data-src') or img.get('src')
                if image_url and image_url.startswith('data:'):
                    image_url = None
            
            # Product ID
            product_id = None
            parent = soup.find('div', {'data-iid': True})
            if parent:
                product_id = parent.get('data-iid')
            
            return {
                'title': title,
                'price': price,
                'original_price': original_price,
                'merchant': merchant,
                'rating': rating,
                'review_count': reviews,
                'image_url': image_url,
                'product_id': product_id
            }
        
        except Exception as e:
            print(f"⚠️  Error parsing product: {e}")
            return None
    
    def _parse_with_regex(self, html: str) -> List[Dict]:
        """
        Parse products using REGEX (Google Maps agent's approach)
        Data is embedded as escaped JSON in the HTML
        """
        products = []
        
        # Patterns for extracting data from embedded JSON
        title_patterns = [
            r'"title":"([^"]+)"',
            r'\\"title\\":\\"([^\\]+)\\"',
        ]
        
        price_patterns = [
            r'\\\\"\\$(\d+(?:,\d{3})*(?:\.\d{2})?)\\\\"',  # Escaped: \\"$1,299.99\\"
            r'"price":"?\$?(\d+(?:,\d{3})*(?:\.\d{2})?)"?',  # "price":"1299.99"
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,299.99
        ]
        
        merchant_patterns = [
            r'"merchant":"([^"]+)"',
            r'\\"merchant\\":\\"([^\\]+)\\"',
        ]
        
        # Extract ALL occurrences
        titles = []
        for pattern in title_patterns:
            titles.extend(re.findall(pattern, html))
        
        prices_raw = []
        for pattern in price_patterns:
            prices_raw.extend(re.findall(pattern, html))
        
        # Convert prices to floats
        prices = []
        for p in prices_raw:
            try:
                prices.append(float(p.replace(',', '')))
            except ValueError:
                pass
        
        merchants = []
        for pattern in merchant_patterns:
            merchants.extend(re.findall(pattern, html))
        
        # Combine data
        max_len = max(len(titles), len(prices))
        for i in range(max_len):
            if i < len(titles) or i < len(prices):
                products.append({
                    'title': titles[i] if i < len(titles) else None,
                    'price': prices[i] if i < len(prices) else None,
                    'original_price': None,
                    'merchant': merchants[i] if i < len(merchants) else None,
                    'rating': None,
                    'review_count': None,
                    'image_url': None,
                    'product_id': None
                })
        
        return products
    
    def search(self, query: str, zipcode: str = None, limit: int = 20) -> List[Dict]:
        """
        Search Google Shopping for products using session pool.
        
        This is the NEW session-based approach:
        1. Get a valid callback session from the pool
        2. Modify the query parameter
        3. Make fast request with curl_cffi
        4. Parse products with our working parser
        
        Args:
            query: Product to search for (e.g., "milk", "eggs")
            zipcode: Optional ZIP code for location-based results
            limit: Max number of results to return
            
        Returns:
            List of product dictionaries
        """
        logger.info(f"🔍 Searching for: {query} (region={self.region})")
        
        # Step 1: Get a valid session from the pool
        callback_session = self.session_manager.get_valid_session(region=self.region)
        
        if not callback_session:
            logger.error(f"❌ No valid callback session available for region={self.region}")
            return []
        
        logger.info(f"Using session {callback_session.id} (age={callback_session.to_dict()['age_minutes']:.1f}min)")
        
        # Step 2: Modify the callback URL with our query
        # The callback URL looks like: /async/callback:6948?fc=...&q=laptop&...
        # We need to replace the q= parameter
        callback_url = callback_session.url
        if '&q=' in callback_url or '?q=' in callback_url:
            # Replace existing query
            import re
            callback_url = re.sub(r'[&?]q=[^&]*', f'&q={query}', callback_url)
        else:
            # Add query parameter
            callback_url = callback_url + f'&q={query}'
        
        # Make full URL
        if not callback_url.startswith('http'):
            full_url = f"https://www.google.com{callback_url}"
        else:
            full_url = callback_url
        
        logger.info(f"Requesting: {full_url[:100]}...")
        
        # Step 3: Make request with curl_cffi (fast!)
        response = self._make_request(full_url)
        
        if not response:
            logger.error("❌ Failed to fetch data")
            self.session_manager.mark_failure(callback_session, "Request failed")
            return []
        
        logger.info(f"✅ Got response ({len(response.text):,} bytes)")
        
        # Step 4: Parse products with BeautifulSoup (our working method)
        soup = BeautifulSoup(response.text, 'html.parser')
        containers = soup.find_all('div', class_='liKJmf')
        
        logger.info(f"📦 Found {len(containers)} product containers")
        
        if len(containers) == 0:
            # No products - session might be expired
            logger.warning("⚠️  No products found - session may be expired")
            self.session_manager.mark_failure(callback_session, "No products returned")
            return []
        
        # Parse products
        products = []
        for container in containers[:limit]:
            product_data = self._parse_product(container)
            if product_data and product_data.get('title') and product_data.get('price'):
                products.append(product_data)
        
        logger.info(f"✅ Parsed {len(products)} valid products")
        
        # Mark session as successful
        self.session_manager.mark_success(callback_session)
        
        return products
    
    def search_with_callback_url(self, callback_url: str) -> List[Dict]:
        """
        Fast search using pre-captured callback URL
        (For testing or when you have a known callback URL)
        """
        print(f"🚀 FAST MODE: Using callback URL")
        
        response = self._make_request(callback_url)
        
        if not response:
            return []
        
        # Remove XSSI protection
        content = response.text
        if content.startswith(')]}\''):
            content = content[4:]
        
        # Parse products
        soup = BeautifulSoup(content, 'html.parser')
        containers = soup.find_all('div', class_='liKJmf')
        
        products = []
        for container in containers:
            product_data = self._parse_product(container)
            if product_data and product_data.get('title') and product_data.get('price'):
                products.append(product_data)
        
        print(f"✅ Parsed {len(products)} products")
        
        return products


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Example of how to use the scraper with proxies"""
    
    # Option 1: Without proxies (may get blocked)
    print("=" * 80)
    print("OPTION 1: No Proxies")
    print("=" * 80)
    scraper = GoogleShoppingScraper()
    products = scraper.search("milk", zipcode="90210", limit=5)
    
    for i, p in enumerate(products, 1):
        print(f"{i}. {p['title']} - ${p['price']} @ {p['merchant']}")
    
    # Option 2: With ISP proxies (recommended for production)
    print("\n" + "=" * 80)
    print("OPTION 2: With ISP Proxies")
    print("=" * 80)
    
    proxy_list = [
        "123.45.67.89:8080",
        "98.76.54.32:8080"
    ]
    
    pool = ProxyPool.from_list(proxy_list)
    scraper = GoogleShoppingScraper(proxy_pool=pool)
    
    products = scraper.search("eggs", zipcode="10001", limit=5)
    
    for i, p in enumerate(products, 1):
        print(f"{i}. {p['title']} - ${p['price']} @ {p['merchant']}")
    
    # Show proxy stats
    print("\n" + "=" * 80)
    print("PROXY STATS")
    print("=" * 80)
    stats = pool.get_stats()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    example_usage()

