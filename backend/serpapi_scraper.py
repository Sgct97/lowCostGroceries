"""
SerpAPI Scraper - Drop-in replacement for uc_scraper.py

This module provides a scraper that uses SerpAPI instead of browser automation,
while maintaining 100% compatibility with the existing API interface.

Key Features:
- Identical interface to UCGoogleShoppingScraper
- Same product format and data structure
- Supports prioritize_nearby toggle
- Proper error handling with fallbacks
- No external indication of using SerpAPI
"""

import os
import logging
import time
import csv
from typing import List, Dict, Optional
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Load ZIP code database for ZIP and city fallback
def _load_zip_database():
    """
    Load ZIP database and create prefix lookup for fallback.
    
    Returns:
        Dictionary mapping ZIP prefix (3 digits) to (first_zipcode, city, state)
        Example: "102" → ("10201", "New York", "New York")
    """
    zip_lookup = {}
    csv_path = os.path.join(os.path.dirname(__file__), 'zip_database.csv')
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                zipcode = row.get('zipcode', '').strip()
                city = row.get('city', '').strip()
                state = row.get('state', '').strip()
                
                if zipcode and city and state and len(zipcode) == 5:
                    prefix = zipcode[:3]  # First 3 digits
                    # Only store first occurrence of each prefix
                    # First ZIP in each prefix is typically a major city
                    if prefix not in zip_lookup:
                        zip_lookup[prefix] = (zipcode, city, state)
        
        logger.info(f"✅ Loaded ZIP database: {len(zip_lookup)} prefixes")
    except Exception as e:
        logger.warning(f"⚠️  Could not load ZIP database: {e}")
    
    return zip_lookup

# Global ZIP lookup (loaded once at module init)
ZIP_PREFIX_LOOKUP = _load_zip_database()

class SerpAPIGoogleShoppingScraper:
    """
    Google Shopping scraper using SerpAPI.
    
    This class mimics the interface of UCGoogleShoppingScraper exactly,
    allowing it to be a drop-in replacement without any API changes.
    """
    
    def __init__(self):
        """Initialize the SerpAPI scraper"""
        self.api_key = os.getenv('SERPAPI_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_KEY environment variable not set")
        
        logger.info("✅ SerpAPI scraper initialized")
    
    def _search_by_city(self, query: str, zipcode: str, city: str, state: str, prioritize_nearby: bool) -> List[Dict]:
        """
        Search SerpAPI using city name for location, but keeping original ZIP in query.
        This is used as a fallback when ZIP is unsupported.
        
        Args:
            query: Search query
            zipcode: Original ZIP code (kept in query string)
            city: City name (used in location parameter)
            state: State name (used in location parameter)
            prioritize_nearby: Whether to prioritize nearby results
            
        Returns:
            List of product dictionaries
        """
        try:
            # Keep original query format with ZIP, only change location parameter
            full_query = f"{query.lower()} near, {zipcode} nearby"
            
            logger.info(f"🔍 SerpAPI city search: '{full_query}' (location: {city}, {state})")
            
            # Build SerpAPI parameters - ONLY location uses city/state
            params = {
                "engine": "google_shopping",
                "q": full_query,
                "location": f"{city}, {state}, United States",
                "api_key": self.api_key,
                "num": 20,
                "no_cache": "true"
            }
            
            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check for errors
            if "error" in results:
                logger.error(f"❌ City search error: {results.get('error')}")
                return []
            
            # Extract and filter products (same logic as ZIP search)
            shopping_results = results.get("shopping_results", [])
            
            if not shopping_results:
                logger.warning(f"⚠️  No results for city search: {city}, {state}")
                return []
            
            logger.info(f"📦 Got {len(shopping_results)} results from city search")
            
            # Parse and filter products (reuse existing method)
            products = self._parse_products(shopping_results, prioritize_nearby)
            
            logger.info(f"✅ City search returned {len(products)} products")
            
            return products[:20]  # Limit to 20
            
        except Exception as e:
            logger.error(f"❌ City search exception: {e}")
            return []
    
    def _get_nearby_zips(self, zipcode: str, max_attempts: int = 10) -> list:
        """
        Get nearby ZIP codes in expanding radius for fallback when original ZIP is unsupported.
        
        Args:
            zipcode: Original 5-digit ZIP code
            max_attempts: Maximum number of fallback ZIPs to try (default: 10)
            
        Returns:
            List of nearby ZIP codes in expanding pattern: [zip-1, zip+1, zip-2, zip+2, ...]
            
        Examples:
            10281 → [10280, 10282, 10279, 10283, 10278, 10284, 10277, 10285, 10276, 10286]
            60614 → [60613, 60615, 60612, 60616, 60611, 60617, 60610, 60618, 60609, 60619]
        """
        try:
            zip_int = int(zipcode)
            nearby = []
            
            # Generate ZIPs in expanding radius pattern
            for offset in range(1, (max_attempts // 2) + 1):
                nearby.append(str(zip_int - offset).zfill(5))  # ZIP - offset
                nearby.append(str(zip_int + offset).zfill(5))  # ZIP + offset
            
            return nearby[:max_attempts]  # Limit to max_attempts
        except (ValueError, TypeError):
            logger.warning(f"⚠️  Cannot generate nearby ZIPs for non-numeric ZIP: {zipcode}")
            return []
    
    def search(
        self, 
        query: str, 
        zipcode: str, 
        prioritize_nearby: bool = True,
        _retry_count: int = 0
    ) -> List[Dict]:
        """
        Search Google Shopping for products.
        
        Args:
            query: Product search query (e.g., "whole milk gallon")
            zipcode: ZIP code for location-based search
            prioritize_nearby: If True, filter to in-store only. If False, include all sources.
            _retry_count: Internal retry counter (do not set manually)
        
        Returns:
            List of product dictionaries with keys:
                - name: Product name
                - price: Price as float
                - merchant: Store name
                - rating: Product rating (optional)
                - review_count: Number of reviews (optional)
        """
        import time
        
        try:
            # Format query for nearby results (SerpAPI format)
            # Critical: Must use "query near, ZIP nearby" format to get in-store results
            full_query = f"{query.lower()} near, {zipcode} nearby"
            
            attempt_info = f" (attempt {_retry_count + 1}/3)" if _retry_count > 0 else ""
            logger.info(f"🔍 SerpAPI search: '{full_query}' (prioritize_nearby={prioritize_nearby}){attempt_info}")
            
            # Build SerpAPI parameters
            params = {
                "engine": "google_shopping",
                "q": full_query,
                "location": f"{zipcode}, United States",  # SerpAPI resolves ZIP to state automatically
                "google_domain": "google.com",
                "hl": "en",
                "gl": "us",
                "api_key": self.api_key,
                "num": 20,  # Get up to 20 results (reduced to avoid junk)
                "no_cache": "true"  # Force fresh results to avoid stale cache
            }
            
            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check for errors
            if "error" in results:
                error_msg = results.get("error", "Unknown error")
                
                # Check if this is an "Unsupported location" error (permanent)
                if "Unsupported" in error_msg and "location" in error_msg:
                    logger.warning(f"⚠️  SerpAPI error: ZIP {zipcode} is unsupported - {error_msg}")
                    
                    # Two-level fallback (only on first attempt)
                    if _retry_count == 0:
                        # Extract ZIP prefix (first 3 digits)
                        zip_prefix = zipcode[:3] if len(zipcode) >= 3 else None
                        
                        if zip_prefix and zip_prefix in ZIP_PREFIX_LOOKUP:
                            fallback_zip, city, state = ZIP_PREFIX_LOOKUP[zip_prefix]
                            
                            # Level 1: Try first ZIP with same prefix
                            if fallback_zip and fallback_zip != zipcode:
                                logger.info(f"🔄 Fallback Level 1: ZIP {zipcode} → ZIP {fallback_zip}")
                                zip_results = self.search(query, fallback_zip, prioritize_nearby, _retry_count=99)
                                if zip_results:
                                    logger.info(f"✅ ZIP fallback to {fallback_zip} successful! Found {len(zip_results)} products.")
                                    return zip_results
                                else:
                                    logger.warning(f"⚠️  ZIP {fallback_zip} also failed or had no results")
                            
                            # Level 2: Try city search as final fallback
                            logger.info(f"🔄 Fallback Level 2: ZIP {zipcode} → {city}, {state} (city search)")
                            city_results = self._search_by_city(query, zipcode, city, state, prioritize_nearby)
                            if city_results:
                                logger.info(f"✅ City fallback to {city}, {state} successful! Found {len(city_results)} products.")
                                return city_results
                        
                        logger.error(f"❌ All fallback attempts failed. No results for unsupported ZIP {zipcode}")
                        return []
                    else:
                        # Already in a fallback attempt, don't recurse further
                        return []
                
                # For other errors (rate limiting, API down, etc), use retry logic
                if _retry_count < 2:  # Max 3 attempts
                    wait_time = 2 ** _retry_count  # Exponential backoff: 1s, 2s
                    logger.warning(f"⚠️  SerpAPI error: {error_msg}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    return self.search(query, zipcode, prioritize_nearby, _retry_count + 1)
                else:
                    logger.error(f"❌ SerpAPI error after 3 attempts: {error_msg}")
                    return []
            
            # Extract shopping results
            shopping_results = results.get("shopping_results", [])
            
            if not shopping_results:
                logger.warning(f"⚠️  No results found for '{query}' in {zipcode}")
                
                # Retry if we got no results from SerpAPI at all
                if _retry_count < 2:
                    wait_time = 2 ** _retry_count
                    logger.warning(f"⚠️  Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    return self.search(query, zipcode, prioritize_nearby, _retry_count + 1)
                
                return []
            
            logger.info(f"📦 Got {len(shopping_results)} total results from SerpAPI")
            
            # Parse and filter products
            products = self._parse_products(shopping_results, prioritize_nearby)
            
            logger.info(f"✅ Returning {len(products)} products (after filtering)")
            
            # CRITICAL: Retry if filtering returned 0 products (when prioritizing nearby)
            if len(products) == 0 and prioritize_nearby and _retry_count < 2:
                wait_time = 2 ** _retry_count
                logger.warning(f"⚠️  Filtering returned 0 in-store products. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self.search(query, zipcode, prioritize_nearby, _retry_count + 1)
            
            return products
        
        except Exception as e:
            logger.error(f"❌ Unexpected error in SerpAPI search: {e}")
            return []
    
    def _parse_products(
        self, 
        shopping_results: List[Dict], 
        prioritize_nearby: bool
    ) -> List[Dict]:
        """
        Parse SerpAPI results into our standard product format.
        
        Args:
            shopping_results: Raw results from SerpAPI
            prioritize_nearby: Whether to filter for in-store only
        
        Returns:
            List of parsed products
        """
        products = []
        
        for item in shopping_results:
            # Extract basic fields
            title = item.get("title", "")
            price = item.get("extracted_price", 0)
            source = item.get("source", "")
            extensions = item.get("extensions", [])
            
            # Skip if missing critical data
            if not title or price <= 0 or not source:
                continue
            
            # Check if product is in-store or nearby
            # Matches: "In store, Tampa", "Nearby, 8 mi", "Also nearby", etc.
            is_in_store = any(
                "in store" in str(ext).lower() or 
                "nearby" in str(ext).lower() or 
                "also nearby" in str(ext).lower()
                for ext in extensions
            )
            
            # DEBUG: Log what extensions we're seeing
            if extensions:
                logger.info(f"   🔍 {source}: extensions={extensions}, is_in_store={is_in_store}")
            
            # Filter based on prioritize_nearby setting
            if prioritize_nearby and not is_in_store:
                continue  # Skip online-only products when prioritizing nearby
            
            # Build product dict in our standard format
            product = {
                "name": title,
                "price": float(price),
                "merchant": source,
                "rating": item.get("rating", None),
                "review_count": item.get("reviews", None),
                "location": None  # Will be populated if in-store
            }
            
            # Add location info if in-store or nearby
            if is_in_store:
                location_info = next(
                    (ext for ext in extensions if 
                     "in store" in str(ext).lower() or 
                     "nearby" in str(ext).lower() or 
                     "also nearby" in str(ext).lower()), 
                    None
                )
                if location_info:
                    # Extract from "In store, City", "Nearby, X mi", or "Also nearby" format
                    product["location"] = location_info
                    logger.debug(f"   📍 {source}: {location_info}")
            
            products.append(product)
        
        # Sort by price (lowest first)
        products.sort(key=lambda x: x['price'])
        
        return products
    
    def close(self):
        """
        Close the scraper (for interface compatibility).
        SerpAPI doesn't need cleanup, but we provide this for compatibility.
        """
        logger.info("🔒 SerpAPI scraper closed")


# Singleton instance for reuse
_scraper_instance = None

def get_scraper() -> SerpAPIGoogleShoppingScraper:
    """
    Get or create a singleton scraper instance.
    
    Returns:
        SerpAPIGoogleShoppingScraper instance
    """
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = SerpAPIGoogleShoppingScraper()
    return _scraper_instance


if __name__ == "__main__":
    # Test the scraper
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("🧪 TESTING SERPAPI SCRAPER")
    print("=" * 80)
    
    scraper = get_scraper()
    
    # Test 1: With prioritize_nearby=True
    print("\n1️⃣ Test: prioritize_nearby=True")
    results_nearby = scraper.search("large eggs", "33773", prioritize_nearby=True)
    print(f"   Found {len(results_nearby)} in-store products")
    if results_nearby:
        print(f"   Lowest: ${results_nearby[0]['price']:.2f} at {results_nearby[0]['merchant']}")
    
    # Test 2: With prioritize_nearby=False
    print("\n2️⃣ Test: prioritize_nearby=False")
    results_all = scraper.search("large eggs", "33773", prioritize_nearby=False)
    print(f"   Found {len(results_all)} total products")
    if results_all:
        print(f"   Lowest: ${results_all[0]['price']:.2f} at {results_all[0]['merchant']}")
    
    print("\n✅ Tests complete!")

