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
    properties: Dict[str, str] = Field(default_factory=dict)
    images: List[HttpUrl] = Field(default_factory=list)
    price: Optional[float] = None
    currency: Optional[str] = None
    availability: Optional[str] = None
    variants: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)
    
    # System fields
    product_id: str
    content_hash: str
    first_seen_at: datetime
    last_seen_at: datetime
