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
from typing import List, Dict, Optional
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

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
    
    def search(
        self, 
        query: str, 
        zipcode: str, 
        prioritize_nearby: bool = True
    ) -> List[Dict]:
        """
        Search Google Shopping for products.
        
        Args:
            query: Product search query (e.g., "whole milk gallon")
            zipcode: ZIP code for location-based search
            prioritize_nearby: If True, filter to in-store only. If False, include all sources.
        
        Returns:
            List of product dictionaries with keys:
                - name: Product name
                - price: Price as float
                - merchant: Store name
                - rating: Product rating (optional)
                - review_count: Number of reviews (optional)
        """
        try:
            # Format query for nearby results (SerpAPI format)
            # Critical: Must use "query near, ZIP nearby" format to get in-store results
            full_query = f"{query.lower()} near, {zipcode} nearby"
            
            logger.info(f"🔍 SerpAPI search: '{full_query}' (prioritize_nearby={prioritize_nearby})")
            
            # Build SerpAPI parameters
            params = {
                "engine": "google_shopping",
                "q": full_query,
                "location": f"{zipcode}, United States",  # SerpAPI resolves ZIP to state automatically
                "google_domain": "google.com",
                "hl": "en",
                "gl": "us",
                "api_key": self.api_key,
                "num": 20  # Get up to 20 results (reduced to avoid junk)
            }
            
            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check for errors
            if "error" in results:
                error_msg = results.get("error", "Unknown error")
                logger.error(f"❌ SerpAPI error: {error_msg}")
                return []
            
            # Extract shopping results
            shopping_results = results.get("shopping_results", [])
            
            if not shopping_results:
                logger.warning(f"⚠️  No results found for '{query}' in {zipcode}")
                return []
            
            logger.info(f"📦 Got {len(shopping_results)} total results from SerpAPI")
            
            # Parse and filter products
            products = self._parse_products(shopping_results, prioritize_nearby)
            
            logger.info(f"✅ Returning {len(products)} products (after filtering)")
            
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

