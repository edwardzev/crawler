from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any
from datetime import datetime

class Product(BaseModel):
    """Canonical Product Schema"""
    supplier: str
    supplier: str
    url: HttpUrl
    url_clean: Optional[str] = None
    title: str
    sku: Optional[str] = None
    category_path: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    color: Optional[str] = None
    properties: Dict[str, str] = Field(default_factory=dict)
    images: List[HttpUrl] = Field(default_factory=list)
    price: Optional[float] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    variants: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)
    
    # System fields
    catalog_id: str  # New Primary Key
    sku_clean: str
    supplier_slug: str
    product_id: Optional[str] = None # Standardized: supplier:sku
    legacy_hash_id: Optional[str] = None # Old SHA1 ID
    content_hash: str
    first_seen_at: datetime
    last_seen_at: datetime
