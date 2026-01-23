#!/usr/bin/env python3
"""
Update existing products with price and category data
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
    parser = argparse.ArgumentParser(description="Update Crawler - Refresh all products")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--db", type=str, default="products.db")
    args = parser.parse_args()
    
    config = load_config(args.config)
    config['db_path'] = str(Path(args.db).resolve())
    
    base_url = config.get('base_url')
    logger.info(f"Starting UPDATE crawl for {config.get('supplier')}")
    
    # Get all product URLs
    sitemap_crawler = SitemapCrawler(base_url)
    product_urls = sitemap_crawler.get_product_urls()
    
    if not product_urls:
        logger.error("No URLs found")
        return
    
    logger.info(f"Will update {len(product_urls)} products")
    
    fetcher = HTMLFetcher()
    pipeline = DataPipeline(config['db_path'])
    
    processed = 0
    errors = 0
    
    for idx, url in enumerate(product_urls, 1):
        try:
            import time
            time.sleep(0.5)  # Faster for updates
            
            if idx % 50 == 0:
                logger.info(f"Progress: {idx}/{len(product_urls)} | Processed: {processed} | Errors: {errors}")
            
            html = fetcher.fetch(url)
            if not html:
                errors += 1
                continue
            
            parser = HTMLParser(html)
            product_data = parser.parse_product(config.get("selectors", {}))
            
            if product_data:
                product_data['url'] = url
                product_data['supplier'] = config.get("supplier")
                
                # Price cleaning
                if product_data.get('price') and isinstance(product_data['price'], str):
                    try:
                        import re
                        clean_price = re.sub(r'[^\d.]', '', product_data['price'])
                        product_data['price'] = float(clean_price) if clean_price else None
                    except ValueError:
                        product_data['price'] = None
                
                # Image URLs
                if product_data.get('images'):
                    if isinstance(product_data['images'], str):
                        product_data['images'] = [product_data['images']]
                    product_data['images'] = [urljoin(url, img) for img in product_data['images'] if img]
                
                if product_data.get('properties') and not isinstance(product_data['properties'], dict):
                    product_data['properties'] = {}
                
                pipeline.process_item(product_data)
                processed += 1
            else:
                errors += 1
                
        except Exception as e:
            logger.error(f"Error: {e}")
            errors += 1
    
    logger.info(f"UPDATE Complete!")
    logger.info(f"Processed: {processed}")
    logger.info(f"Errors: {errors}")

if __name__ == "__main__":
    main()
