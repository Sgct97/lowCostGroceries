"""
Low Cost Groceries API
FastAPI backend for finding cheapest groceries
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import time
from datetime import datetime
import logging

# Import our production UC scraper
from uc_scraper import search_products as scrape_google_shopping

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Low Cost Groceries API",
    description="Find the cheapest groceries using Google Shopping",
    version="1.0.0"
)

# CORS middleware (allow frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SearchRequest(BaseModel):
    """Request to search for products"""
    query: str = Field(..., description="Product to search for (e.g., 'milk', 'eggs')")
    zipcode: str = Field(..., description="ZIP code for location-based search")
    limit: int = Field(default=20, ge=1, le=100, description="Max number of results")

class Product(BaseModel):
    """Product information"""
    title: str
    price: float
    original_price: Optional[float] = None
    merchant: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    image_url: Optional[str] = None
    product_id: Optional[str] = None
    
    @property
    def savings(self) -> Optional[float]:
        """Calculate savings if on sale"""
        if self.original_price and self.original_price > self.price:
            return self.original_price - self.price
        return None
    
    @property
    def savings_percent(self) -> Optional[float]:
        """Calculate savings percentage"""
        if self.savings and self.original_price:
            return (self.savings / self.original_price) * 100
        return None

class SearchResponse(BaseModel):
    """Response with products"""
    query: str
    zipcode: str
    products: List[Product]
    total_found: int
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)

class CartRequest(BaseModel):
    """Request to build a shopping cart"""
    items: List[str] = Field(..., description="List of products to find")
    zipcode: str

class CartResponse(BaseModel):
    """Shopping cart with cheapest options"""
    items: Dict[str, Product]  # item_name -> cheapest_product
    total_cost: float
    total_savings: float
    store_breakdown: Dict[str, float]  # merchant -> subtotal


# ============================================================================
# IN-MEMORY CACHE (Simple for now, will add Redis later)
# ============================================================================

cache: Dict[str, SearchResponse] = {}
CACHE_TTL = 3600  # 1 hour

def get_cache_key(query: str, zipcode: str) -> str:
    """Generate cache key"""
    return f"{query.lower().strip()}:{zipcode}:{int(time.time() // CACHE_TTL)}"

def get_from_cache(query: str, zipcode: str) -> Optional[SearchResponse]:
    """Try to get results from cache"""
    key = get_cache_key(query, zipcode)
    return cache.get(key)

def save_to_cache(query: str, zipcode: str, response: SearchResponse):
    """Save results to cache"""
    key = get_cache_key(query, zipcode)
    cache[key] = response


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Low Cost Groceries API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search",
            "cart": "/cart",
            "docs": "/docs"
        }
    }

@app.post("/search", response_model=SearchResponse)
async def search_products_endpoint(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Search for products by query and location
    
    Returns cached results if available (< 1 hour old),
    otherwise scrapes Google Shopping using UC
    """
    
    # Check cache first
    cached_response = get_from_cache(request.query, request.zipcode)
    if cached_response:
        logger.info(f"✅ Cache hit: {request.query} in {request.zipcode}")
        cached_response.cached = True
        return cached_response
    
    logger.info(f"🔍 Cache miss - scraping: {request.query} in {request.zipcode}")
    
    try:
        # Use our proven UC scraper
        scrape_results = scrape_google_shopping(
            search_terms=[request.query],
            zip_code=request.zipcode,
            max_products_per_item=request.limit,
            use_parallel=False  # Single search, no need for parallel
        )
        
        # Extract products for this query
        raw_products = scrape_results.get(request.query, [])
        
        # Convert to Pydantic models
        products = [
            Product(
                title=p.get('name'),
                price=p.get('price'),
                original_price=None,  # Not available in aria-label parsing
                merchant=p.get('merchant', 'Unknown'),
                rating=p.get('rating'),
                review_count=p.get('review_count'),
                image_url=None,  # Not available in aria-label parsing
                product_id=None
            )
            for p in raw_products
            if p.get('name') and p.get('price')
        ]
        
        response = SearchResponse(
            query=request.query,
            zipcode=request.zipcode,
            products=products[:request.limit],
            total_found=len(products),
            cached=False
        )
        
        # Save to cache
        save_to_cache(request.query, request.zipcode, response)
        
        logger.info(f"✅ Scraped {len(products)} products for '{request.query}'")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Scraping failed for '{request.query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape products: {str(e)}"
        )

@app.post("/cart", response_model=CartResponse)
async def build_cart(request: CartRequest):
    """
    Build a shopping cart with the cheapest option for each item
    
    Uses PARALLEL scraping for multiple items (FAST!)
    Recommended: 2-3 parallel browsers per droplet
    """
    
    logger.info(f"🛒 Building cart: {len(request.items)} items in ZIP {request.zipcode}")
    
    # Check cache for each item first
    cached_items = {}
    items_to_scrape = []
    
    for item in request.items:
        cached = get_from_cache(item, request.zipcode)
        if cached:
            cached_items[item] = cached.products
        else:
            items_to_scrape.append(item)
    
    logger.info(f"✅ Cache: {len(cached_items)} items | 🔍 Scraping: {len(items_to_scrape)} items")
    
    # Scrape uncached items in PARALLEL
    scraped_items = {}
    if items_to_scrape:
        try:
            scrape_results = scrape_google_shopping(
                search_terms=items_to_scrape,
                zip_code=request.zipcode,
                max_products_per_item=20,
                use_parallel=True  # Use parallel for multiple items!
            )
            
            # Convert to Product models and cache
            for item, raw_products in scrape_results.items():
                products = [
                    Product(
                        title=p.get('name'),
                        price=p.get('price'),
                        original_price=None,
                        merchant=p.get('merchant', 'Unknown'),
                        rating=p.get('rating'),
                        review_count=p.get('review_count'),
                        image_url=None,
                        product_id=None
                    )
                    for p in raw_products
                    if p.get('name') and p.get('price')
                ]
                scraped_items[item] = products
                
                # Cache for future requests
                response = SearchResponse(
                    query=item,
                    zipcode=request.zipcode,
                    products=products,
                    total_found=len(products),
                    cached=False
                )
                save_to_cache(item, request.zipcode, response)
        
        except Exception as e:
            logger.error(f"❌ Parallel scraping failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to scrape products: {str(e)}"
            )
    
    # Combine cached + scraped results
    all_results = {**cached_items, **scraped_items}
    
    # Build cart with cheapest options
    items_dict = {}
    total_cost = 0.0
    total_savings = 0.0
    store_breakdown = {}
    
    for item in request.items:
        products = all_results.get(item, [])
        
        if products:
            # Get cheapest product
            cheapest = min(products, key=lambda p: p.price)
            items_dict[item] = cheapest
            total_cost += cheapest.price
            
            # Calculate savings
            if cheapest.savings:
                total_savings += cheapest.savings
            
            # Track by store
            merchant = cheapest.merchant
            store_breakdown[merchant] = store_breakdown.get(merchant, 0) + cheapest.price
        else:
            logger.warning(f"⚠️  No products found for '{item}'")
    
    logger.info(f"✅ Cart built: {len(items_dict)} items, ${total_cost:.2f} total")
    
    return CartResponse(
        items=items_dict,
        total_cost=round(total_cost, 2),
        total_savings=round(total_savings, 2),
        store_breakdown=store_breakdown
    )

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get detailed information about a specific product"""
    # TODO: Implement product details
    raise HTTPException(status_code=501, detail="Product details endpoint not yet implemented")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(cache),
        "uptime": "unknown"  # TODO: Track uptime
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info"
    )

