"use client";

import { useState } from "react";
import { Product } from "@/lib/types";
import { ProductGrid } from "./ProductGrid";
import { ProductFilters } from "./ProductFilters";

interface CategoryContentProps {
    products: Product[];
}

export function CategoryContent({ products }: CategoryContentProps) {
    const [filteredProducts, setFilteredProducts] = useState<Product[]>(products);

    return (
        <div className="flex flex-col md:flex-row gap-8">
            <div className="md:w-64 flex-shrink-0">
                <ProductFilters 
                    products={products} 
                    onFilterChange={setFilteredProducts}
                />
            </div>

            <div className="flex-1">
                <ProductGrid products={filteredProducts} />
            </div>
        </div>
    );
}
