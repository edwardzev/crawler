import logging
from collections import deque
from typing import Set, Dict, Any
from urllib.parse import urlparse, urljoin
from crawler.fetcher import HTMLFetcher
from crawler.parser import HTMLParser
from crawler.pipeline import DataPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrawlerEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url")
        self.allowed_domains = set(config.get("allowed_domains", []))
        self.queue = deque([self.base_url])
        self.visited: Set[str] = set()
        self.visited_skus: Set[str] = set()
        
        # Threading support
        import threading
        self.lock = threading.Lock()
        self.num_workers = config.get("num_workers", 3)
        
        # Shared setup
        db_path = config.get('db_path', 'products.db')
        self.pipeline = DataPipeline(db_path)
        self._load_existing_skus(db_path)
        self.consecutive_failures = 0
        self.MAX_CONSECUTIVE_FAILURES = 5

    def _load_existing_skus(self, db_path: str):
        try:
            import sqlite3
            import os
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT sku FROM products WHERE sku IS NOT NULL")
                rows = cursor.fetchall()
                for row in rows:
                    if row[0]:
                        self.visited_skus.add(row[0].upper())
                conn.close()
                logger.info(f"Loaded {len(self.visited_skus)} existing SKUs from DB.")
        except Exception as e:
            logger.error(f"Failed to load existing SKUs: {e}")

    def seed_queue(self, urls: list[str]):
        """Append external URLs to the queue with normalization"""
        with self.lock:
            for url in urls:
                normalized_url = url.split("#")[0]
                if normalized_url not in self.visited:
                    self.queue.append(normalized_url)
            
            # Shuffle to distribute workers
            import random
            temp_list = list(self.queue)
            random.shuffle(temp_list)
            self.queue = deque(temp_list)

    def seed_from_db(self):
        """Seed queue with all URLs currently in the products database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.pipeline.db_path)
            cursor = conn.cursor()
            # Select url or source_url
            cursor.execute("SELECT url FROM products WHERE url IS NOT NULL")
            rows = cursor.fetchall()
            urls = [row[0] for row in rows if row[0].startswith("http")]
            conn.close()
            
            logger.info(f"DB Seeding: Found {len(urls)} product URLs.")
            self.seed_queue(urls)
        except Exception as e:
            logger.error(f"Failed to seed from DB: {e}")

    def run(self):
        logger.info(f"Starting multi-threaded crawl with {self.num_workers} workers at {self.base_url}")
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        start_time = time.time()
        self.count = 0
        
        def worker():
            fetcher = HTMLFetcher()
            try:
                while True:
                    url = None
                    with self.lock:
                        if not self.queue:
                            break
                        url = self.queue.popleft()
                        if url in self.visited:
                            continue
                        self.visited.add(url)
                    
                    try:
                        self._process_url(url, fetcher)
                    except Exception as e:
                        logger.error(f"Worker error processing {url}: {e}")
                    
                    with self.lock:
                        self.count += 1
                        if self.count % 10 == 0:
                            elapsed = time.time() - start_time
                            rate = self.count / elapsed if elapsed > 0 else 0
                            logger.info(f"--- STATUS: {self.count} pages processed | Queue: {len(self.queue)} | Rate: {rate:.2f} p/s ---")
            finally:
                fetcher.close()

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(worker) for _ in range(self.num_workers)]
            for future in futures:
                future.result()

    def _process_url(self, url: str, fetcher: HTMLFetcher):
        logger.info(f"Processing: {url}")
        
        use_dynamic = self.config.get("use_dynamic", False)
        html = None
        
        try:
            if use_dynamic:
                html = fetcher.fetch_dynamic(url)
            else:
                html = fetcher.fetch(url)
                
            if not html:
                self.consecutive_failures += 1
                logger.warning(f"Failed to fetch {url} (Consecutive failures: {self.consecutive_failures})")
                return

            self.consecutive_failures = 0

            # ADDED: Smaller random delay for throughput
            import time
            import random
            time.sleep(random.uniform(0.5, 1.5))

            parser = HTMLParser(html)
            
            if self._is_product_url(url):
                product_data = parser.parse_product(self.config.get("selectors", {}))
                
                if product_data.get('title'):
                    title = product_data['title']
                    title_lower = title.lower()
                    if any(x in title_lower for x in ["403", "forbidden", "access denied", "robot challenge", "bot detection", "screen reader"]):
                        logger.warning(f"Detected Blocked Page (Title: '{title}') for {url}, skipping ingestion.")
                        return
                    
                if product_data:
                    product_data['url'] = url
                    product_data['supplier'] = self.config.get("supplier")
                    
                    if not product_data.get('sku'):
                        product_data['sku'] = self._extract_sku_from_url(url)
                    
                    if product_data.get('price') and isinstance(product_data['price'], str):
                        import re
                        try:
                            clean_price = re.sub(r'[^\d.]', '', product_data['price'])
                            product_data['price'] = float(clean_price) if clean_price else None
                        except ValueError:
                            product_data['price'] = None

                    if product_data.get('images'):
                        if isinstance(product_data['images'], str):
                            product_data['images'] = [product_data['images']]
                        product_data['images'] = [urljoin(url, img) for img in product_data['images'] if img]
                        
                    if product_data.get('properties') and not isinstance(product_data['properties'], dict):
                        product_data['properties'] = {}
                    
                    if product_data.get('sku'):
                        with self.lock:
                            self.visited_skus.add(product_data['sku'].upper())

                    if product_data.get('variants'):
                        # Normalize string variants to dicts and filter out placeholders
                        norm_variants = []
                        for v in product_data['variants']:
                            if isinstance(v, str):
                                if v.strip() in ["צבע", "בחר צבע", "בחר"]:
                                    continue
                                norm_variants.append({"name": v.strip()})
                            else:
                                norm_variants.append(v)
                        product_data['variants'] = norm_variants

                    # DEBUG: Log images before saving
                    logger.info(f"DEBUG: About to save product {product_data.get('sku')} with {len(product_data.get('images', []))} images: {product_data.get('images', [])[:2]}")
                    
                    self.pipeline.process_item(product_data)
            
            with self.lock:
                q_len = len(self.queue)
            
            if q_len < 500:
                links = parser.extract_links(url)
                for link in links:
                    link = link.split("#")[0]
                    if self._can_crawl(link):
                        with self.lock:
                            if link not in self.visited:
                                self.queue.append(link)
                                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

    def _is_product_url(self, url: str) -> bool:
        patterns = self.config.get("product_url_patterns", [])
        for p in patterns:
            if p.startswith("regex:"):
                import re
                if re.search(p[6:], url):
                    return True
            elif p in url:
                return True
        return False

    def _extract_sku_from_url(self, url: str) -> str:
        import re
        sku_regex = self.config.get("sku_url_regex")
        if sku_regex:
            match = re.search(sku_regex, url)
            if match:
                return match.group(1)
        return ""

    def _can_crawl(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc and parsed.netloc not in self.allowed_domains:
            return False
            
        cat_patterns = self.config.get("category_url_patterns", [])
        prod_patterns = self.config.get("product_url_patterns", [])
        
        is_category = False
        for p in cat_patterns:
            if p.startswith("regex:"):
                import re
                if re.search(p[6:], url):
                    is_category = True
                    break
            elif p in url:
                is_category = True
                break

        is_product = False
        for p in prod_patterns:
            if p.startswith("regex:"):
                import re
                if re.search(p[6:], url):
                    is_product = True
                    break
            elif p in url:
                is_product = True
                break
        
        if "add-to-cart" in url:
            return False
            
        if is_product:
            # Check for incremental mode
            if self.config.get("incremental", False):
                sku = self._extract_sku_from_url(url)
                # If we couldn't extract SKU from URL, we might still crawl to be safe, 
                # or skip if strict. defaulting to crawl.
                if sku:
                   with self.lock:
                       if sku.upper() in self.visited_skus:
                           logger.info(f"Skipping existing SKU (Incremental): {sku}")
                           return False
            return True
            
        if is_category:
            if url == self.base_url: return True
            with self.lock:
                if len(self.queue) > 500: 
                    return False
            return True

        return url == self.base_url
