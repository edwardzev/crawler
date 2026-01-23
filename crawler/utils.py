import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent identity:
    - Lowercase hostname
    - Remove fragments
    - Remove tracking parameters
    - Standardize trailing slash
    """
    if not url:
        return ""
        
    try:
        parsed = urlparse(url)
        
        # 1. Lowercase netloc (hostname)
        netloc = parsed.netloc.lower()
        
        # 2. Filter query parameters
        # Remove common tracking params
        TRACKING_PARAMS = {
            'gclid', 'fbclid', 'yclid', 'mc_cid', 'mc_eid', 
            'ref', 'refid', 'source', 'campaign', 'ad_id'
        }
        
        query_params = []
        for key, value in parse_qsl(parsed.query):
            k_lower = key.lower()
            if k_lower in TRACKING_PARAMS or k_lower.startswith('utm_'):
                continue
            query_params.append((key, value))
            
        # Sort params for stability
        query_params.sort()
        new_query = urlencode(query_params)
        
        # 3. Path normalization (trailing slash)
        path = parsed.path
        if path != '/' and path.endswith('/'):
            path = path.rstrip('/')
            
        # Reconstruct
        # scheme, netloc, url, params, query, fragment
        return urlunparse((
            parsed.scheme, 
            netloc, 
            path, 
            parsed.params, 
            new_query, 
            '' # Remove fragment
        ))
    except Exception:
        # Fallback for very broken URLs
        return url

def generate_product_id(supplier: str, sku: str, url: str) -> str:
    """
    Generate stable Product ID using SHA1.
    Priority: Supplier + Clean SKU -> Supplier + Clean URL
    """
    clean_url = normalize_url(url)
    
    if sku and sku.strip():
        # Clean SKU: uppercase, strip whitespace
        identifier = f"{supplier}|{sku.strip().upper()}"
    else:
        identifier = f"{supplier}|{clean_url}"
        
    return hashlib.sha1(identifier.encode('utf-8')).hexdigest()

def generate_content_hash(data: dict) -> str:
    """
    Generate hash of content fields only, excluding timestamps.
    Used to detect material changes in product data.
    """
    # Fields that define the "content" of the product
    CONTENT_FIELDS = [
        'supplier', 'title', 'sku', 'category_path', 
        'description', 'properties', 'images', 
        'price', 'currency', 'availability', 'variants'
        # Explicitly EXCLUDING: first_seen_at, last_seen_at, url (ID), raw
    ]
    
    # Extract only content fields in stable order
    content_map = {}
    for field in CONTENT_FIELDS:
        val = data.get(field)
        # Normalize lists/dicts to strings for hashing stability
        if isinstance(val, (list, dict)):
            import json
            val = json.dumps(val, sort_keys=True, default=str)
        content_map[field] = str(val) if val is not None else ""
        
    # Sort by keys to ensure deterministic order
    content_str = "|".join(f"{k}:{content_map[k]}" for k in sorted(content_map.keys()))
    
    return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

