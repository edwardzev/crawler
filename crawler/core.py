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
        
        # Initialize components
        self.fetcher = HTMLFetcher()
        # Parser will be instantiated per response or reused if stateless
        db_path = config.get('db_path', 'products.db')
        self.pipeline = DataPipeline(db_path)
        self._load_existing_skus(db_path)

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
                        self.visited_skus.add(row[0].upper()) # Normalize to upper case
                conn.close()
                logger.info(f"Loaded {len(self.visited_skus)} existing SKUs from DB.")
        except Exception as e:
            logger.error(f"Failed to load existing SKUs: {e}")
        
    def run(self):
        logger.info(f"Starting crawl at {self.base_url}")
        
        while self.queue:
            url = self.queue.popleft()
            
            if url in self.visited:
                continue
                
            self.visited.add(url)
            self._process_url(url)
            
    def _process_url(self, url: str):
        logger.info(f"Processing: {url}")
        
        # Determine if we need dynamic fetching (simple check for now)
        # In real logic, might depend on config keys or failures
        try:
            html = self.fetcher.fetch(url) # Start with static
            if not html: 
                logger.warning(f"Failed to fetch {url}")
                return

            parser = HTMLParser(html)
            
            # Check if product page
            if self._is_product_url(url):
                logger.info(f"Found product page: {url}")
                product_data = parser.parse_product(self.config.get("selectors", {}))
                if product_data:
                    product_data['url'] = url
                    product_data['supplier'] = self.config.get("supplier")
                    
                    # Basic cleaning
                    if product_data.get('price') and isinstance(product_data['price'], str):
                        try:
                            # Remove all non-numeric except dots (handles ₪, $, €, commas, etc)
                            import re
                            clean_price = re.sub(r'[^\d.]', '', product_data['price'])
                            product_data['price'] = float(clean_price) if clean_price else None
                        except ValueError:
                            product_data['price'] = None
                            
                    if product_data.get('images'):
                        if isinstance(product_data['images'], str):
                            product_data['images'] = [product_data['images']]
                        # Resolve relative URLs
                        product_data['images'] = [urljoin(url, img) for img in product_data['images'] if img]
                        
                    if product_data.get('properties') and not isinstance(product_data['properties'], dict):
                        # TODO: proper table parsing
                        product_data['properties'] = {}
                    
                    # Add to visited SKUs if found
                    if product_data.get('sku'):
                        self.visited_skus.add(product_data['sku'].upper())

                    self.pipeline.process_item(product_data)
            
            # Discovery: Extract new links
            links = parser.extract_links(url) # We need to add this method to Parser
            logger.info(f"Extracted {len(links)} links from {url}")
            for link in links:
                if self._can_crawl(link):
                    logger.info(f"Queueing: {link}")
                    self.queue.append(link)
                else:
                    logger.debug(f"Skipping: {link}")
                    
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

    def _is_product_url(self, url: str) -> bool:
        patterns = self.config.get("product_url_patterns", [])
        return any(p in url for p in patterns)

    def _extract_sku_from_url(self, url: str) -> str:
        # Heuristic: Extract first segment after /product/
        # e.g. /product/sku123-desc... -> sku123
        try:
            path = urlparse(url).path
            if "/product/" in path:
                # Get part after /product/
                slug = path.split("/product/")[-1]
                # Get part before first hyphen
                if "-" in slug:
                    return slug.split("-")[0].upper()
                # Fallback if no hyphen (unlikely based on data)
                return slug.strip("/").upper()
        except:
            pass
        return ""

    def _can_crawl(self, url: str) -> bool:
        if url in self.visited: 
            return False
            
        parsed = urlparse(url)
        # Domain check
        domain_valid = any(parsed.netloc.endswith(d) for d in self.allowed_domains)
        if not domain_valid:
            return False
            
        # Pattern check (if category patterns exist, mainly follow those + products)
        # For now, simple logic: if it's a product or category or next page
        cat_patterns = self.config.get("category_url_patterns", [])
        prod_patterns = self.config.get("product_url_patterns", [])
        
        is_category = any(p in url for p in cat_patterns)
        is_product = any(p in url for p in prod_patterns)
        
        # Ignore add-to-cart links
        if "add-to-cart" in url:
            return False

        if is_product:
            # OPTIMIZATION: Check if we have this SKU already
            sku = self._extract_sku_from_url(url)
            if sku and sku in self.visited_skus:
                # logger.debug(f"Skipping known SKU: {sku} in {url}")
                return False
        
        return is_category or is_product or url == self.base_url

