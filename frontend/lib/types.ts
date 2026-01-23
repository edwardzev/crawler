export interface Product {
    id: string;
    supplier: string;
    url: string;
    url_clean?: string;
    slug: string;
    title: string;
    sku: string;
    category_path: string[];
    category_slug_path: string[];
    description?: string;
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
