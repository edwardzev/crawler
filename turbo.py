#!/usr/bin/env python3
"""
Turbo Crawler - Uses sitemap.xml for instant product discovery
"""
import argparse
import yaml
import logging
from pathlib import Path
from crawler.sitemap import SitemapCrawler
from crawler.fetcher import HTMLFetcher
from crawler.parser import HTMLParser
from crawler.pipeline import DataPipeline
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Turbo Crawler (Sitemap Mode)")
    parser.add_argument("--config", type=str, required=True, help="Path to supplier config YAML")
    parser.add_argument("--db", type=str, default="products.db", help="Path to SQLite DB")
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return
        
    config = load_config(config_path)
    db_path = Path(args.db).resolve()
    config['db_path'] = str(db_path)
    
    base_url = config.get('base_url')
    logger.info(f"Starting TURBO crawl for {config.get('supplier', 'Unknown Supplier')}")
    
    # Step 1: Get all product URLs from sitemap
    sitemap_crawler = SitemapCrawler(base_url)
    product_urls = sitemap_crawler.get_product_urls()
    
    if not product_urls:
        logger.error("No product URLs found in sitemap. Exiting.")
        return
    
    logger.info(f"Sitemap contains {len(product_urls)} product URLs")
    
    # Step 2: Set up fetcher and pipeline
    fetcher = HTMLFetcher()
    pipeline = DataPipeline(str(db_path))
    
    # Load existing SKUs to skip duplicates
    import sqlite3
    import os
    visited_skus = set()
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sku FROM products WHERE sku IS NOT NULL")
            rows = cursor.fetchall()
            for row in rows:
                if row[0]:
                    visited_skus.add(row[0].upper())
            conn.close()
            logger.info(f"Loaded {len(visited_skus)} existing SKUs from DB.")
        except Exception as e:
            logger.error(f"Failed to load existing SKUs: {e}")
    
    # Step 3: Crawl each product URL
    processed = 0
    skipped = 0
    errors = 0
    
    for idx, url in enumerate(product_urls, 1):
        # Extract SKU from URL for quick skip check
        try:
            from crawler.core import CrawlerEngine
            # Create a temp instance just to use the helper method
            temp = CrawlerEngine.__new__(CrawlerEngine)
            sku = temp._extract_sku_from_url(url) if hasattr(CrawlerEngine, '_extract_sku_from_url') else ""
            
            if sku and sku in visited_skus:
                skipped += 1
                if idx % 100 == 0:
                    logger.info(f"Progress: {idx}/{len(product_urls)} | Processed: {processed} | Skipped: {skipped} | Errors: {errors}")
                continue
        except:
            pass
        
        # Fetch and parse
        try:
            import time
            time.sleep(1)  # Rate limiting: 1 second between requests
            
            logger.info(f"[{idx}/{len(product_urls)}] Processing: {url}")
            html = fetcher.fetch(url)
            if not html:
                logger.warning(f"Failed to fetch {url}")
                errors += 1
                continue
            
            parser = HTMLParser(html)
            product_data = parser.parse_product(config.get("selectors", {}))
            
            if product_data:
                product_data['url'] = url
                product_data['supplier'] = config.get("supplier")
                
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
                    product_data['images'] = [urljoin(url, img) for img in product_data['images'] if img]
                
                if product_data.get('properties') and not isinstance(product_data['properties'], dict):
                    product_data['properties'] = {}
                
                pipeline.process_item(product_data)
                
                # Add to visited SKUs
                if product_data.get('sku'):
                    visited_skus.add(product_data['sku'].upper())
                
                processed += 1
            else:
                logger.warning(f"No product data extracted from {url}")
                errors += 1
                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            errors += 1
        
        # Progress update every 100 items
        if idx % 100 == 0:
            logger.info(f"Progress: {idx}/{len(product_urls)} | Processed: {processed} | Skipped: {skipped} | Errors: {errors}")
    
    logger.info(f"TURBO Crawl Complete!")
    logger.info(f"Total URLs: {len(product_urls)}")
    logger.info(f"Processed: {processed}")
    logger.info(f"Skipped (already in DB): {skipped}")
    logger.info(f"Errors: {errors}")
    logger.info("Done.")

if __name__ == "__main__":
    main()
