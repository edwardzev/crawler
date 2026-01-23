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
    
    if not args.no_crawl:
        print(f"Starting crawler for {config.get('supplier', 'Unknown Supplier')}")
        engine = CrawlerEngine(config)
        engine.run()
        
    if args.export:
        print(f"Exporting data to {args.export}...")
        from crawler.pipeline import DataPipeline
        pipeline = DataPipeline(db_path)
        pipeline.export_data(args.export, fmt=args.format)
        print("Done.")

if __name__ == "__main__":
    main()
