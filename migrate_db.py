
import logging
from crawler.pipeline import DataPipeline

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_db_migration():
    """
    Execute the database hardening migration.
    This will:
    1. Update schema with url_clean
    2. Normalize all URLs
    3. Generate stable, SKU-based IDs
    4. Deduplicate records
    """
    db_path = "products.db"
    
    print(f"Starting migration for: {db_path}")
    print("-----------------------------------")
    
    try:
        pipeline = DataPipeline(db_path)
        pipeline.run_migration()
        print("\n✅ Migration complete successfully.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")

if __name__ == "__main__":
    run_db_migration()
