"use client";

import { useState, useCallback } from "react";
import { Product } from "@/lib/types";
import { ProductGrid } from "./ProductGrid";
import { ProductFilters } from "./ProductFilters";

interface CategoryContentProps {
    products: Product[];
}

export function CategoryContent({ products }: CategoryContentProps) {
    const [filteredProducts, setFilteredProducts] = useState<Product[]>(products);

    const handleFilterChange = useCallback((filtered: Product[]) => {
        setFilteredProducts(filtered);
    }, []);

    return (
        <div className="flex flex-col md:flex-row gap-8 flex-1">
            <div className="md:w-64 flex-shrink-0">
                <ProductFilters 
                    products={products} 
                    onFilterChange={handleFilterChange}
                />
            </div>

            <div className="flex-1">
                <ProductGrid products={filteredProducts} />
            </div>
        </div>
    );
}
