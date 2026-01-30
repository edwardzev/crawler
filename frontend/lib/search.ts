import MiniSearch from "minisearch";
import { Product } from "./types";

export interface SearchResult extends Product {
    score: number;
    match: {
        [key: string]: string[];
    };
}

// Global instance to reuse index execution
let miniSearch: MiniSearch<Product> | null = null;

export function initSearchIndex(products: Product[]) {
    if (miniSearch) return miniSearch;

    miniSearch = new MiniSearch({
        fields: ["title", "sku", "search_blob", "supplier"], // fields to index for full-text search
        storeFields: [
            "id",
            "title",
            "sku",
            "slug",
            "image_main",
            "category_slug_path",
            "supplier",
            "price",
            "currency",
        ], // fields to return with search results
        searchOptions: {
            boost: { sku: 2, title: 1.5 },
            fuzzy: 0.2,
            prefix: true,
        },
        idField: "id",
    });

    const seenIds = new Set();
    const uniqueProducts = products.filter(p => {
        if (seenIds.has(p.id)) return false;
        seenIds.add(p.id);
        return true;
    });

    miniSearch.addAll(uniqueProducts);
    return miniSearch;
}

export function searchProducts(
    products: Product[],
    query: string
): SearchResult[] {
    if (!query) return [];
    const index = initSearchIndex(products);
    // @ts-ignore - MiniSearch types are slightly loose with return values, but this is safe
    return index.search(query) as SearchResult[];
}
