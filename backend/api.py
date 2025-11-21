"""
Low Cost Groceries API
FastAPI backend for finding cheapest groceries

Uses Redis job queue for async scraping (no timeouts, handles 1000s of users)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import time
from datetime import datetime
import logging
import redis
import uuid
import json
import os

# Import our production UC scraper (for direct mode if needed)
from uc_scraper import search_products as scrape_google_shopping

# Import AI service for product clarification
from ai_service import clarify_item

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# REDIS CONNECTION
# ============================================================================

# Connect to Redis (job queue + results storage)
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))

try:
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        socket_connect_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info(f"✅ Connected to Redis at {redis_host}:{redis_port}")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis: {e}")
    logger.warning("⚠️  API will run in DIRECT mode (no queue, slower, no concurrency)")
    redis_client = None

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
    prioritize_nearby: bool = Field(default=True, description="Prioritize stores nearby over best prices")

class CartResponse(BaseModel):
    """Shopping cart with cheapest options"""
    items: Dict[str, Product]  # item_name -> cheapest_product
    total_cost: float
    total_savings: float
    store_breakdown: Dict[str, float]  # merchant -> subtotal

class ClarifyRequest(BaseModel):
    """Request to clarify a vague grocery item using AI"""
    item: str = Field(..., description="Vague grocery item (e.g., 'milk', 'eggs')")
    context: Optional[List[str]] = Field(default=None, description="Previously clarified items for context-aware suggestions")

class ClarifyResponse(BaseModel):
    """AI-powered product clarification response"""
    status: str
    suggested: Dict
    alternatives: List[Dict]
    processing_time: Optional[float] = None


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
            "clarify": "/api/clarify",
            "search": "/search",
            "cart": "/api/cart",
            "results": "/api/results/{job_id}",
            "docs": "/docs"
        }
    }

@app.post("/api/clarify", response_model=ClarifyResponse)
async def clarify_product_endpoint(request: ClarifyRequest):
    """
    AI-powered product clarification using GPT-5-mini
    
    Converts vague grocery items into specific, searchable products.
    
    Example:
        Input: {"item": "milk"}
        Output: {
            "suggested": {"name": "Whole Milk, 1 Gallon", "confidence": 0.95, "emoji": "🥛"},
            "alternatives": [
                {"name": "2% Milk, 1 Gallon", "emoji": "🥛"},
                {"name": "Skim Milk, 1 Gallon", "emoji": "🥛"}
            ]
        }
    
    Context-aware: Pass previously clarified items in 'context' field for smarter suggestions
    (e.g., if user picked organic eggs, suggest organic milk)
    """
    
    if not request.item or len(request.item.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Item cannot be empty"
        )
    
    logger.info(f"🤖 AI clarification request: '{request.item}' (context: {len(request.context or [])} items)")
    
    start_time = time.time()
    
    try:
        # Call GPT-5-mini for clarification
        result = await clarify_item(
            item=request.item.strip(),
            context=request.context
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"✅ AI suggested: '{result['suggested']['name']}' ({processing_time:.2f}s)")
        
        return {
            "status": "success",
            "suggested": result.get('suggested', {}),
            "alternatives": result.get('alternatives', []),
            "processing_time": round(processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"❌ AI clarification failed: {e}")
        
        # Return fallback suggestion
        processing_time = time.time() - start_time
        return {
            "status": "error",
            "suggested": {
                "name": f"{request.item.title()}, 1 Unit",
                "confidence": 0.5,
                "emoji": "🛒"
            },
            "alternatives": [],
            "processing_time": round(processing_time, 2)
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

@app.post("/api/cart")
async def submit_cart(request: CartRequest):
    """
    Submit a cart for scraping - returns job_id instantly
    
    QUEUE MODE (default with Redis):
    - Job added to Redis queue
    - Returns job_id immediately (< 100ms)
    - Client polls GET /results/{job_id} to get results
    - Workers process jobs in background
    
    DIRECT MODE (if Redis unavailable):
    - Scrapes immediately (blocks for 20-30s)
    - Returns results directly
    """
    
    logger.info(f"🛒 Cart submitted: {len(request.items)} items in ZIP {request.zipcode}")
    
    # QUEUE MODE (with Redis)
    if redis_client:
        try:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            # Create job data
            job_data = {
                'job_id': job_id,
                'items': request.items,
                'zip_code': request.zipcode,  # CRITICAL: User's location
                'prioritize_nearby': request.prioritize_nearby,  # User's preference
                'submitted_at': datetime.now().isoformat(),
                'max_products_per_item': 50
            }
            
            # Push to Redis queue
            redis_client.lpush('scrape_queue', json.dumps(job_data))
            
            # Set initial status
            redis_client.setex(
                f'status:{job_id}',
                3600,  # 1 hour expiry
                json.dumps({
                    'status': 'queued',
                    'submitted_at': job_data['submitted_at'],
                    'zip_code': request.zipcode,
                    'items': request.items
                })
            )
            
            # Estimate time based on queue size
            queue_length = redis_client.llen('scrape_queue')
            estimated_time = len(request.items) * 2  # ~2s per item
            
            logger.info(f"✅ Job {job_id[:8]}... queued (queue length: {queue_length})")
            
            return {
                'job_id': job_id,
                'status': 'queued',
                'estimated_time_seconds': estimated_time,
                'queue_position': queue_length,
                'message': f'Job queued. Poll GET /results/{job_id} for results.'
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to queue job: {e}")
            logger.warning("⚠️  Falling back to DIRECT mode...")
            # Fall through to direct mode
    
    # DIRECT MODE (no Redis or Redis failed)
    logger.info("⚙️  Running in DIRECT mode (blocking scrape)...")
    
    try:
        scrape_results = scrape_google_shopping(
            search_terms=request.items,
            zip_code=request.zipcode,
            max_products_per_item=50,
            use_parallel=False  # Sequential is safer for direct mode
        )
        
        # Convert to response format
        items_dict = {}
        total_cost = 0.0
        store_breakdown = {}
        
        for item in request.items:
            products = scrape_results.get(item, [])
            
            if products:
                # Get cheapest product
                cheapest_raw = min(products, key=lambda p: p['price'])
                cheapest = Product(
                    title=cheapest_raw.get('name'),
                    price=cheapest_raw.get('price'),
                    merchant=cheapest_raw.get('merchant', 'Unknown'),
                    rating=cheapest_raw.get('rating'),
                    review_count=cheapest_raw.get('review_count')
                )
                items_dict[item] = cheapest
                total_cost += cheapest.price
                
                # Track by store
                merchant = cheapest.merchant
                store_breakdown[merchant] = store_breakdown.get(merchant, 0) + cheapest.price
        
        return {
            'status': 'complete',
            'mode': 'direct',
            'results': {
                'items': items_dict,
                'total_cost': round(total_cost, 2),
                'total_savings': 0.0,
                'store_breakdown': store_breakdown
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Direct scraping failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape products: {str(e)}"
        )


@app.get("/api/results/{job_id}")
async def get_job_results(job_id: str):
    """
    Get results for a queued job
    
    Responses:
    - {"status": "queued"} - Job waiting in queue
    - {"status": "processing", "progress": "..."} - Job being scraped
    - {"status": "complete", "results": {...}} - Job done!
    - {"status": "failed", "error": "..."} - Job failed
    - {"status": "not_found"} - Job ID invalid or expired
    """
    
    if not redis_client:
        raise HTTPException(
            status_code=501,
            detail="Results endpoint requires Redis. API is running in DIRECT mode."
        )
    
    # Check for completed results first
    result = redis_client.get(f'result:{job_id}')
    if result:
        result_data = json.loads(result)
        
        if result_data.get('status') == 'complete':
            # Convert results to proper format
            results = result_data.get('results', {})
            
            # DEBUG: Log first product's price
            if results:
                first_item = list(results.keys())[0]
                if results[first_item]:
                    first_price = results[first_item][0].get('price')
                    logger.info(f"📊 API returning results - First product price: ${first_price} ({type(first_price)})")
            
            return {
                'status': 'complete',
                'results': results,
                'zip_code': result_data.get('zip_code'),
                'total_time': result_data.get('total_time'),
                'worker_id': result_data.get('worker_id'),
                'completed_at': result_data.get('completed_at')
            }
        else:
            # Failed
            return {
                'status': 'failed',
                'error': result_data.get('error', 'Unknown error'),
                'worker_id': result_data.get('worker_id')
            }
    
    # Check status
    status = redis_client.get(f'status:{job_id}')
    if status:
        status_data = json.loads(status)
        return {
            'status': status_data.get('status'),
            'zip_code': status_data.get('zip_code'),
            'items': status_data.get('items'),
            'submitted_at': status_data.get('submitted_at'),
            'started_at': status_data.get('started_at'),
            'worker_id': status_data.get('worker_id')
        }
    
    # Not found
    return {
        'status': 'not_found',
        'message': 'Job ID not found or expired (results kept for 1 hour)'
    }

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

