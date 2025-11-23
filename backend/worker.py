#!/usr/bin/env python3
"""
Production Worker with Flexible Scraper Backend
Pulls jobs from Redis queue and scrapes products

CRITICAL: Preserves location-specific scraping by passing ZIP code to every search

Supports two scraper backends:
- SerpAPI (fast, reliable, no blocking) - DEFAULT
- UC Browser (fallback, slower but proven)

Controlled by SCRAPER_BACKEND environment variable
"""

import redis
import json
import time
import logging
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import scraper based on environment variable
SCRAPER_BACKEND = os.getenv('SCRAPER_BACKEND', 'serpapi').lower()

if SCRAPER_BACKEND == 'serpapi':
    from serpapi_scraper import get_scraper
    USING_SERPAPI = True
else:
    from uc_scraper import UCGoogleShoppingScraper
    USING_SERPAPI = False

# Configure logging BEFORE any log messages
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Output to stdout
        logging.StreamHandler(sys.stderr)   # Also to stderr for systemd
    ]
)
logger = logging.getLogger(__name__)

# Log which backend we're using (after logging is configured!)
if USING_SERPAPI:
    logger.info("🚀 Using SerpAPI scraper backend")
else:
    logger.info("🌐 Using UC Browser scraper backend")


class PersistentBrowserWorker:
    """
    Worker that maintains a persistent UC browser to avoid startup overhead
    
    Key features:
    - Browser stays warm between jobs (4s faster per job)
    - Auto-restart every 50 jobs or 30 minutes (prevent detection)
    - Health checks ensure browser is responsive
    - ALWAYS passes user's ZIP code to scraper (CRITICAL!)
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, worker_id: str = None):
        """
        Initialize worker
        
        Args:
            redis_host: Redis server hostname/IP
            redis_port: Redis server port
            worker_id: Unique identifier for this worker (for logging)
        """
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        self.worker_id = worker_id or f"worker-{os.getpid()}"
        self.scraper = None
        self.browser = None
        self.jobs_completed = 0
        self.browser_start_time = None
        self.max_jobs_per_browser = 50
        self.max_browser_age_seconds = 30 * 60  # 30 minutes
        
        logger.info(f"🚀 {self.worker_id} initialized")
        logger.info(f"   Redis: {redis_host}:{redis_port}")
        logger.info(f"   Browser restart policy: {self.max_jobs_per_browser} jobs OR {self.max_browser_age_seconds/60:.0f} minutes")
        
        # Initialize scraper immediately
        if USING_SERPAPI:
            logger.info("🔧 Initializing SerpAPI scraper...")
            self.scraper = get_scraper()
            self.browser = None
            logger.info("✅ SerpAPI scraper ready!")
        else:
            # UC Browser will be initialized on first job (via _start_browser)
            logger.info("🌐 UC Browser will be initialized on first job")
    
    def _should_restart_browser(self) -> bool:
        """Check if browser should be restarted"""
        # SerpAPI doesn't use browser, no restarts needed
        if USING_SERPAPI:
            return False
        
        if not self.browser or not self.browser_start_time:
            return True
        
        # Check job count
        if self.jobs_completed >= self.max_jobs_per_browser:
            logger.info(f"🔄 Browser restart: {self.jobs_completed} jobs completed (limit: {self.max_jobs_per_browser})")
            return True
        
        # Check age
        age = time.time() - self.browser_start_time
        if age >= self.max_browser_age_seconds:
            logger.info(f"🔄 Browser restart: {age/60:.1f} minutes old (limit: {self.max_browser_age_seconds/60:.0f})")
            return True
        
        return False
    
    def _start_browser(self):
        """Start a new UC browser instance (or initialize SerpAPI scraper)"""
        try:
            if self.browser and not USING_SERPAPI:
                logger.info("🛑 Closing old browser...")
                try:
                    self.browser.quit()
                except:
                    pass
            
            if USING_SERPAPI:
                # SerpAPI doesn't need browser setup
                logger.info("🚀 Initializing SerpAPI scraper...")
                start = time.time()
                
                self.scraper = get_scraper()
                self.browser = None  # No browser needed
                
                elapsed = time.time() - start
                logger.info(f"✅ SerpAPI scraper ready in {elapsed:.3f}s")
                
                self.browser_start_time = time.time()
                self.jobs_completed = 0
            else:
                # UC Browser setup (original code)
                logger.info("🌐 Starting new UC browser...")
                logger.info(f"   DISPLAY env: {os.environ.get('DISPLAY', 'not set')}")
                logger.info(f"   XVFB env: {os.environ.get('XVFB', 'not set')}")
                start = time.time()
                
                # Check if running in server environment
                use_xvfb = os.environ.get('DISPLAY') is None or os.environ.get('XVFB') == '1'
                logger.info(f"   use_xvfb: {use_xvfb}")
                
                self.scraper = UCGoogleShoppingScraper(use_xvfb=use_xvfb)
                logger.info("   Scraper object created, setting up driver...")
                
                self.browser = self.scraper._setup_driver()
                
                elapsed = time.time() - start
                logger.info(f"✅ Browser ready in {elapsed:.1f}s (xvfb={use_xvfb})")
                
                self.browser_start_time = time.time()
                self.jobs_completed = 0
            
        except Exception as e:
            logger.error(f"❌ Failed to start browser: {e}", exc_info=True)
            self.browser = None
            raise
    
    def _ensure_browser_ready(self):
        """Ensure browser is ready, restart if needed"""
        if self._should_restart_browser():
            self._start_browser()
    
    def process_job(self, job_data: Dict) -> Dict:
        """
        Process a single scraping job
        
        CRITICAL: Extracts ZIP code from job and passes to scraper
        
        Args:
            job_data: Dict with keys: job_id, items (list), zip_code, max_products_per_item
        
        Returns:
            Dict with results or error
        """
        job_id = job_data['job_id']
        items = job_data['items']
        zip_code = job_data['zip_code']  # CRITICAL: User's location
        max_products = job_data.get('max_products_per_item', 20)
        prioritize_nearby = job_data.get('prioritize_nearby', True)  # Default to True for backward compatibility
        
        # LOG THE ZIP CODE (so we can verify it's being used)
        logger.info(f"📋 [{job_id[:8]}] Starting scrape")
        logger.info(f"   Items: {', '.join(items)}")
        logger.info(f"   📍 ZIP CODE: {zip_code} (LOCATION-SPECIFIC)")
        logger.info(f"   🎯 Prioritize Nearby: {prioritize_nearby}")
        logger.info(f"   Max products: {max_products}")
        
        try:
            # Ensure browser is ready
            logger.info(f"[{job_id[:8]}] Ensuring browser is ready...")
            self._ensure_browser_ready()
            logger.info(f"[{job_id[:8]}] Browser ready!")
            
            # Update status to processing
            self.redis_client.setex(
                f'status:{job_id}',
                3600,  # 1 hour TTL
                json.dumps({
                    'status': 'processing',
                    'worker_id': self.worker_id,
                    'started_at': datetime.now().isoformat(),
                    'zip_code': zip_code,  # Include ZIP in status
                    'items': items
                })
            )
            
            # DO THE SCRAPING
            # Use sequential method with persistent browser (FASTEST for 1-10 items)
            start_time = time.time()
            
            results = {}
            for i, item in enumerate(items):
                item_start = time.time()
                
                logger.info(f"[{job_id[:8]}] Scraping item {i+1}/{len(items)}: {item}")
                
                # CRITICAL: Pass ZIP code to every search!
                wait_time = 1 if i == 0 else 0.5  # First search needs more time
                
                try:
                    if USING_SERPAPI:
                        # SerpAPI has different parameters
                        products = self.scraper.search(
                            query=item,
                            zipcode=zip_code,  # ← USER'S ZIP CODE
                            prioritize_nearby=prioritize_nearby  # User's preference
                        )
                    else:
                        # UC Browser scraper parameters
                        products = self.scraper.search(
                            search_term=item,
                            zip_code=zip_code,  # ← USER'S ZIP CODE
                            max_products=max_products,
                            wait_time=wait_time,
                            driver=self.browser,  # Reuse persistent browser
                            close_driver=False,  # Keep browser open!
                            prioritize_nearby=prioritize_nearby  # User's preference
                        )
                    
                    results[item] = products
                    
                    item_elapsed = time.time() - item_start
                    logger.info(f"   ✓ {item}: {len(products)} products ({item_elapsed:.1f}s)")
                    
                except Exception as e:
                    logger.error(f"   ✗ {item}: Scraping failed - {e}", exc_info=True)
                    results[item] = []
            
            elapsed = time.time() - start_time
            
            # Store results in Redis (30 second TTL - NO LONG-TERM CACHE)
            self.redis_client.setex(
                f'result:{job_id}',
                30,  # Just long enough to retrieve results
                json.dumps({
                    'status': 'complete',
                    'results': results,
                    'zip_code': zip_code,
                    'total_time': round(elapsed, 2),
                    'worker_id': self.worker_id,
                    'completed_at': datetime.now().isoformat()
                })
            )
            
            logger.info(f"✅ [{job_id[:8]}] Complete! {len(items)} items in {elapsed:.1f}s")
            
            self.jobs_completed += 1
            
            return {
                'status': 'success',
                'job_id': job_id,
                'elapsed': elapsed
            }
            
        except Exception as e:
            logger.error(f"❌ [{job_id[:8]}] Error: {e}")
            
            # Store error in Redis
            self.redis_client.setex(
                f'result:{job_id}',
                3600,
                json.dumps({
                    'status': 'failed',
                    'error': str(e),
                    'worker_id': self.worker_id,
                    'failed_at': datetime.now().isoformat()
                })
            )
            
            return {
                'status': 'error',
                'job_id': job_id,
                'error': str(e)
            }
    
    def run(self):
        """
        Main worker loop - runs forever
        Pulls jobs from Redis queue and processes them
        """
        logger.info(f"🎯 {self.worker_id} ready, waiting for jobs from Redis...")
        logger.info(f"   Queue: 'scrape_queue'")
        logger.info(f"   Ctrl+C to stop")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                # Block and wait for a job (timeout after 5 seconds)
                logger.info(f"[{self.worker_id}] ⏳ Waiting for job from queue...")
                job = self.redis_client.brpop('scrape_queue', timeout=5)
                
                if job:
                    logger.info(f"[{self.worker_id}] 📥 Job received from queue!")
                    logger.info(f"   Raw job data: {job}")
                    
                    # job is a tuple: (queue_name, job_data)
                    try:
                        job_data = json.loads(job[1])
                        logger.info(f"   Job ID: {job_data.get('job_id', 'unknown')[:16]}...")
                        logger.info(f"   Items: {job_data.get('items', [])}")
                        logger.info(f"   ZIP: {job_data.get('zip_code', 'unknown')}")
                    except Exception as e:
                        logger.error(f"   ❌ Failed to parse job data: {e}")
                        continue
                    
                    # Process the job
                    logger.info(f"[{self.worker_id}] Starting to process job...")
                    result = self.process_job(job_data)
                    logger.info(f"[{self.worker_id}] Job processing complete: {result.get('status')}")
                    
                    # Reset error counter on success
                    if result['status'] == 'success':
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1
                        logger.warning(f"[{self.worker_id}] Job failed. Consecutive errors: {consecutive_errors}")
                    
                else:
                    # No jobs available, just log periodically
                    if self.jobs_completed % 10 == 0 and self.jobs_completed > 0:
                        logger.debug(f"💤 No jobs in queue (completed {self.jobs_completed} jobs so far)")
                
                # Check for too many errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"🛑 Too many consecutive errors ({consecutive_errors}), restarting browser...")
                    self._start_browser()
                    consecutive_errors = 0
                    
            except KeyboardInterrupt:
                logger.info(f"🛑 {self.worker_id} shutting down...")
                break
                
            except redis.ConnectionError as e:
                logger.error(f"❌ Redis connection error: {e}")
                logger.info("   Waiting 10 seconds before retry...")
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Worker error: {e}")
                consecutive_errors += 1
                time.sleep(5)
        
        # Cleanup
        if self.browser and not USING_SERPAPI:
            logger.info("🧹 Closing browser...")
            try:
                self.browser.quit()
            except:
                pass
        elif USING_SERPAPI:
            logger.info("🧹 Closing SerpAPI scraper...")
            try:
                self.scraper.close()
            except:
                pass
        
        logger.info(f"👋 {self.worker_id} stopped (completed {self.jobs_completed} jobs)")


def main():
    """
    Entry point for worker
    
    Environment variables:
    - REDIS_HOST: Redis server hostname (default: localhost)
    - REDIS_PORT: Redis server port (default: 6379)
    - WORKER_ID: Optional worker identifier
    """
    
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = int(os.environ.get('REDIS_PORT', 6379))
    worker_id = os.environ.get('WORKER_ID', None)
    
    logger.info("="*80)
    logger.info("🏭 GOOGLE SHOPPING SCRAPER WORKER")
    logger.info("="*80)
    
    # Create and run worker
    worker = PersistentBrowserWorker(
        redis_host=redis_host,
        redis_port=redis_port,
        worker_id=worker_id
    )
    
    worker.run()


if __name__ == "__main__":
    main()

