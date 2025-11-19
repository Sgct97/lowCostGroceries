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
async def search_products(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Search for products by query and location
    
    Returns cached results if available (< 1 hour old),
    otherwise scrapes Google Shopping
    """
    
    # Check cache first
    cached_response = get_from_cache(request.query, request.zipcode)
    if cached_response:
        cached_response.cached = True
        return cached_response
    
    # TODO: Integrate scraper here
    # For now, return mock data
    mock_products = [
        Product(
            title=f"{request.query.title()} - Mock Product 1",
            price=3.99,
            original_price=4.99,
            merchant="Walmart",
            rating=4.5,
            review_count=1234
        ),
        Product(
            title=f"{request.query.title()} - Mock Product 2",
            price=4.49,
            merchant="Target",
            rating=4.3,
            review_count=567
        )
    ]
    
    response = SearchResponse(
        query=request.query,
        zipcode=request.zipcode,
        products=mock_products[:request.limit],
        total_found=len(mock_products),
        cached=False
    )
    
    # Save to cache
    save_to_cache(request.query, request.zipcode, response)
    
    return response

@app.post("/cart", response_model=CartResponse)
async def build_cart(request: CartRequest):
    """
    Build a shopping cart with the cheapest option for each item
    
    Takes a list of items and finds the cheapest available option for each
    """
    
    items_dict = {}
    total_cost = 0.0
    total_savings = 0.0
    store_breakdown = {}
    
    for item in request.items:
        # Search for each item
        search_req = SearchRequest(query=item, zipcode=request.zipcode, limit=10)
        search_resp = await search_products(search_req, BackgroundTasks())
        
        if search_resp.products:
            # Get cheapest product
            cheapest = min(search_resp.products, key=lambda p: p.price)
            items_dict[item] = cheapest
            total_cost += cheapest.price
            
            # Calculate savings
            if cheapest.savings:
                total_savings += cheapest.savings
            
            # Track by store
            merchant = cheapest.merchant
            store_breakdown[merchant] = store_breakdown.get(merchant, 0) + cheapest.price
    
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

