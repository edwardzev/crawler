import argparse
import yaml
from pathlib import Path
from crawler.core import CrawlerEngine

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Supplier Catalog Crawler")
    parser.add_argument("--config", type=str, required=True, help="Path to supplier config YAML")
    parser.add_argument("--export", type=str, help="Path to export output (e.g. products.csv)")
    parser.add_argument("--format", type=str, default="csv", choices=["csv", "xlsx", "json"], help="Export format")
    parser.add_argument("--db", type=str, default="products.db", help="Path to SQLite DB")
    parser.add_argument("--no-crawl", action="store_true", help="Skip crawling, only export")
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return
        
    config = load_config(config_path)
    # Inject db path into config or handle separately
    db_path = Path(args.db).resolve()
    config['db_path'] = str(db_path)
    
    if not args.no_crawl:
        print(f"Starting crawler for {config.get('supplier', 'Unknown Supplier')}")
        engine = CrawlerEngine(config)
        engine.run()
        
    if args.export:
        print(f"Exporting data to {args.export}...")
        from crawler.pipeline import DataPipeline
        # Use simple string path or the resolved one from above
        # If args.db was relative, resolved one is safer to ensure consistency
        pipeline = DataPipeline(str(Path(args.db).resolve()))
        pipeline.export_data(args.export, fmt=args.format)
        print("Done.")

if __name__ == "__main__":
    main()
