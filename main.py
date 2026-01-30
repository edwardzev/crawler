import argparse
import yaml
from pathlib import Path
from crawler.core import CrawlerEngine

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Supplier Catalog Crawler")
    parser = argparse.ArgumentParser(description="Supplier Catalog Crawler")
    parser.add_argument("--config", type=str, help="Path to supplier config YAML")
    parser.add_argument("--sitemap", action="store_true", help="Seed queue from sitemap.xml")
    parser.add_argument("--incremental", action="store_true", help="Skip already crawled SKUs")
    parser.add_argument("--recrawl", action="store_true", help="Recrawl ALL URLs existing in the DB (ignore discovery)")
    parser.add_argument("--export", type=str, help="Path to export output (e.g. products.csv)")
    parser.add_argument("--format", type=str, default="csv", choices=["csv", "xlsx", "json"], help="Export format")
    parser.add_argument("--db", type=str, default="products.db", help="Path to SQLite DB")
    parser.add_argument("--no-crawl", action="store_true", help="Skip crawling, only export")
    parser.add_argument("--export-frontend", action="store_true", help="Generate frontend-ready JSON snapshots in data/out/")
    args = parser.parse_args()
    
    # Init DB Path
    db_path = str(Path(args.db).resolve())
    
    # Frontend Export Mode (Exit early)
    if args.export_frontend:
        print(f"Starting Frontend Export from {db_path}...")
        from crawler.exporter import FrontendExporter
        exporter = FrontendExporter(db_path, "data/out")
        exporter.export()
        # If no config provided, we can exit here. If config is provided, maybe user wants both?
        # Requirement says "Frontend Export step", implies it acts as an operation.
        return 

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return
        
    config = load_config(config_path)
    config['db_path'] = db_path
    config['incremental'] = args.incremental
    
    if not args.no_crawl:
        print(f"Starting crawler for {config.get('supplier', 'Unknown Supplier')}")
        
        # Initialize Engine
        engine = CrawlerEngine(config)
        
        # Optional: Load from Sitemap first
        if args.recrawl:
             print("Recrawl mode: Loading all known product URLs from DB...")
             engine.seed_from_db()
        elif args.sitemap:
            print(f"Fetching URLs from sitemap: {config.get('sitemap_url')} ...")
            from crawler.sitemap import SitemapCrawler
            sitemap_crawler = SitemapCrawler(config.get('base_url'))
            urls = sitemap_crawler.get_product_urls()
            if urls:
                print(f"Seeding queue with {len(urls)} URLs from sitemap...")
                engine.seed_queue(urls)
            else:
                print("Sitemap blocked or empty. Seeding from Category Patterns in config...")
                cat_patterns = config.get("category_url_patterns", [])
                base = config.get("base_url").rstrip('/')
                seed_urls = [base + p if p.startswith('/') else p for p in cat_patterns if p.startswith('/')]
                engine.seed_queue(seed_urls)

        engine.run()
        
    if args.export:
        print(f"Exporting data to {args.export}...")
        from crawler.pipeline import DataPipeline
        pipeline = DataPipeline(db_path)
        pipeline.export_data(args.export, fmt=args.format)
        print("Done.")

if __name__ == "__main__":
    main()
