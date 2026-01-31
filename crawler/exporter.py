import json
import logging
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from crawler.utils import slugify, normalize_url

logger = logging.getLogger(__name__)

class FrontendExporter:
    """
    Exports database content to frontend-ready JSON files.
    - products.frontend.json (Flat list with SEO slugs)
    - categories.frontend.json (Tree structure)
    - categories.flat.json (Flat category list)
    """
    
    def __init__(self, db_path: str, output_dir: str):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def export(self):
        logger.info(f"Starting Frontend Export from {self.db_path}")
        
        products = self._load_products()
        if not products:
            logger.warning("No products found to export")
            return
            
        processed_products = []
        category_paths = []
        
        for p in products:
            processed = self._process_product(p)
            processed_products.append(processed)
            if processed.get('category_path'):
                category_paths.append(processed['category_path'])
                
        # Write Products
        self._write_json(processed_products, "products.frontend.json")
        
        # Build and Write Categories
        tree, flat = self._build_category_structures(category_paths)
        self._write_json(tree, "categories.frontend.json")
        self._write_json(flat, "categories.flat.json")
        
        logger.info("Frontend Export Complete ✅")

    def _load_products(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM products")
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def _process_product(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw DB row into frontend object"""
        
        # Parse JSON fields
        category_path = self._parse_json_field(raw.get('category_path'), [])
        properties = self._parse_json_field(raw.get('properties'), {})
        images = self._parse_json_field(raw.get('images'), [])
        variants = self._parse_json_field(raw.get('variants'), [])
        
        # Ensure category_path is list of strings
        if isinstance(category_path, str):
            category_path = [category_path]
        
        # Basic fields
        title = raw.get('title') or ""
        sku = raw.get('sku') or ""
        
        # Slugs
        product_slug = slugify(f"{title}-{sku}" if sku else title)
        category_slug_path = [slugify(c) for c in category_path]
        
        # Search Blob
        search_parts = [title, sku] + category_path + list(properties.keys()) + list(properties.values())
        search_blob = " ".join([str(p) for p in search_parts if p])
        
        # Parse variant field (NEW: for ordering flow)
        # Variant is expected to be a JSON string in Airtable with structure:
        # {"type": "color", "options": [{"value": "black", "label": "Black"}, ...]}
        variant = None
        variant_raw = raw.get('variant')
        if variant_raw:
            try:
                variant_parsed = self._parse_json_field(variant_raw, None)
                # Validate structure
                if variant_parsed and isinstance(variant_parsed, dict):
                    if 'type' in variant_parsed and 'options' in variant_parsed:
                        variant = variant_parsed
            except Exception as e:
                logger.warning(f"Failed to parse variant for product {sku}: {e}")
        
        return {
            "id": raw.get('catalog_id') or raw.get('product_id'), # Prefer new ID
            "catalog_id": raw.get('catalog_id'),
            "sku_clean": raw.get('sku_clean'),
            "supplier_slug": raw.get('supplier_slug'),
            "supplier": raw.get('supplier'),
            "url": raw.get('url'),
            "url_clean": raw.get('url_clean'),
            "slug": product_slug,
            "title": title,
            "sku": sku,
            "category_path": category_path,
            "category_slug_path": category_slug_path,
            "description": raw.get('description'),
            "properties": properties,
            "images": images,
            "image_main": images[0] if images else None,
            "price": raw.get('price'),
            "currency": raw.get('currency'),
            "availability": raw.get('availability'),
            "variants": variants,
            "variant": variant,  # NEW: Parsed variant for ordering flow
            "content_hash": raw.get('content_hash'),
            "first_seen_at": str(raw.get('first_seen_at')),
            "last_seen_at": str(raw.get('last_seen_at')),
            "search_blob": search_blob
        }

    def _parse_json_field(self, value: Any, default: Any) -> Any:
        if not value:
            return default
        if isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return default # or return transformed string if schema matches
        return value

    def _build_category_structures(self, all_paths: List[List[str]]):
        """
        Builds both Tree and Flat category structures.
        """
        tree = {"name": "root", "slug": "", "children": []}
        flat_map = {} # path_tuple -> count
        
        for path in all_paths:
            if not path:
                continue
                
            # Update counts for every level
            current_path = []
            for segment in path:
                current_path.append(segment)
                path_tuple = tuple(current_path)
                flat_map[path_tuple] = flat_map.get(path_tuple, 0) + 1
        
        # Build Tree
        # Helper to find or create child node
        def get_child(node, name):
            for child in node['children']:
                if child['name'] == name:
                    return child
            new_child = {"name": name, "slug": slugify(name), "count": 0, "children": []}
            node['children'].append(new_child)
            return new_child

        for path_tuple, count in flat_map.items():
            current_node = tree
            for segment in path_tuple:
                current_node = get_child(current_node, segment)
            current_node['count'] = count # This sets count for the leaf of this specific sub-path
            
        # Recursive count aggregation (optional, or just rely on flat map counts)
        # But wait, flat_map has counts for *visited* paths. 
        # A parent category count should be sum of its direct assignments + children?
        # Requirement says: "count": 123. Usually this implies total products in this node + subnodes.
        # Let's aggregate counts up the tree.
        
        def aggregate_counts(node):
            total = 0
            # If this node represents a path that products actually have (exact match), add that.
            # But our flat_map approach separates them.
            # Simpler approach: Re-iterate paths and increment count for EACH node in path.
            return node
            
        # Re-build tree with simpler logic:
        # 1. Create all nodes
        # 2. Iterate all products again to increment counts
        
        # Reset tree
        tree = {"name": "root", "slug": "", "children": []}
        nodes_ref = {} # slug_path -> node
        
        for path in all_paths:
            current_node = tree
            current_slug_path = ""
            
            for segment in path:
                slug = slugify(segment)
                # Ensure child exists
                found = None
                for child in current_node['children']:
                    if child['slug'] == slug:
                        found = child
                        break
                if not found:
                    found = {"name": segment, "slug": slug, "count": 0, "children": []}
                    current_node['children'].append(found)
                
                # Increment count
                found['count'] += 1
                current_node = found
                
        # Build Flat List from tree traversal or flat_map
        # Requirement: path array, slug_path array, count
        flat_list = []
        
        def traverse(node, path_names, path_slugs):
            if node['name'] != 'root':
                flat_list.append({
                    "path": path_names,
                    "slug_path": path_slugs,
                    "count": node['count']
                })
            
            for child in node['children']:
                traverse(child, path_names + [child['name']], path_slugs + [child['slug']])
                
        traverse(tree, [], [])
        
        return tree, flat_list

    def _write_json(self, data: Any, filename: str):
        path = self.output_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote {path}")
