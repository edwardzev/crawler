export interface Product {
    id: string; // Will now be catalog_id
    catalog_id: string;
    sku_clean: string;
    supplier_slug: string;
    supplier: string;
    url: string;
    url_clean?: string;
    slug: string;
    title: string;
    sku: string;
    category_path: string[];
    category_slug_path: string[];
    description?: string;
    color?: string;
    properties: Record<string, string>;
    images: string[];
    image_main?: string;
    price?: number;
    currency?: string;
    availability?: string;
    variants?: any[];
    content_hash?: string;
    first_seen_at?: string;
    last_seen_at?: string;
    search_blob?: string;
}

export interface OrderItem {
    id: string; // Internal local ID
    product_title: string;
    sku: string;
    slot_index: number;
    width: number;
    quantity: number;
    logo_src: string;
    mockup_src: string;
}

export interface OrderState {
    order_id: string | null;
    items: OrderItem[];
    used_slots: number[]; // 1, 2, 3, 4, 5
}

export interface CategoryNode {
    name: string;
    slug: string;
    count: number;
    children: CategoryNode[];
}

export interface CategoryFlat {
    path: string[];
    slug_path: string[];
    count: number;
}
