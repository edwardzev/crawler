"use client";

import { Product } from "@/lib/types";
import { useState, useEffect, useMemo } from "react";

interface ProductFiltersProps {
    products: Product[];
    onFilterChange: (filtered: Product[]) => void;
}

interface FilterState {
    priceMin: number;
    priceMax: number;
    selectedSuppliers: string[];
}

export function ProductFilters({ products, onFilterChange }: ProductFiltersProps) {
    // Calculate price range from products
    const priceRange = useMemo(() => {
        const prices = products
            .map(p => p.price)
            .filter((p): p is number => typeof p === 'number' && p > 0);
        
        if (prices.length === 0) {
            return { min: 0, max: 1000 };
        }
        
        return {
            min: Math.floor(Math.min(...prices)),
            max: Math.ceil(Math.max(...prices))
        };
    }, [products]);

    // Get unique suppliers with counts
    const supplierCounts = useMemo(() => {
        const counts: Record<string, number> = {};
        products.forEach(p => {
            if (p.supplier) {
                counts[p.supplier] = (counts[p.supplier] || 0) + 1;
            }
        });
        return Object.entries(counts)
            .sort(([a], [b]) => a.localeCompare(b, 'he'))
            .map(([supplier, count]) => ({ supplier, count }));
    }, [products]);

    // Filter state
    const [filterState, setFilterState] = useState<FilterState>({
        priceMin: priceRange.min,
        priceMax: priceRange.max,
        selectedSuppliers: []
    });

    // Update filter state when products change
    useEffect(() => {
        setFilterState({
            priceMin: priceRange.min,
            priceMax: priceRange.max,
            selectedSuppliers: []
        });
    }, [priceRange.min, priceRange.max]);

    // Apply filters
    useEffect(() => {
        const filtered = products.filter(product => {
            // Price filter
            const price = product.price ?? 0;
            if (price < filterState.priceMin || price > filterState.priceMax) {
                return false;
            }

            // Supplier filter (OR logic)
            if (filterState.selectedSuppliers.length > 0) {
                if (!product.supplier || !filterState.selectedSuppliers.includes(product.supplier)) {
                    return false;
                }
            }

            return true;
        });

        onFilterChange(filtered);
    }, [filterState, products, onFilterChange]);

    const handlePriceMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = Number(e.target.value);
        setFilterState(prev => ({
            ...prev,
            priceMin: Math.min(value, prev.priceMax)
        }));
    };

    const handlePriceMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = Number(e.target.value);
        setFilterState(prev => ({
            ...prev,
            priceMax: Math.max(value, prev.priceMin)
        }));
    };

    const handleSupplierToggle = (supplier: string) => {
        setFilterState(prev => ({
            ...prev,
            selectedSuppliers: prev.selectedSuppliers.includes(supplier)
                ? prev.selectedSuppliers.filter(s => s !== supplier)
                : [...prev.selectedSuppliers, supplier]
        }));
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
            {/* Price Filter */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">מחיר</h3>
                <div className="space-y-4">
                    <div className="flex items-center justify-between text-sm text-gray-700">
                        <span>₪{filterState.priceMin.toLocaleString()}</span>
                        <span>–</span>
                        <span>₪{filterState.priceMax.toLocaleString()}</span>
                    </div>
                    
                    <div className="space-y-2">
                        <label className="block">
                            <span className="text-xs text-gray-600">מינימום</span>
                            <input
                                type="range"
                                min={priceRange.min}
                                max={priceRange.max}
                                value={filterState.priceMin}
                                onChange={handlePriceMinChange}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                            />
                        </label>
                        
                        <label className="block">
                            <span className="text-xs text-gray-600">מקסימום</span>
                            <input
                                type="range"
                                min={priceRange.min}
                                max={priceRange.max}
                                value={filterState.priceMax}
                                onChange={handlePriceMaxChange}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                            />
                        </label>
                    </div>
                </div>
            </div>

            {/* Supplier Filter */}
            {supplierCounts.length > 0 && (
                <div className="border-t border-gray-200 pt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">ספק</h3>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                        {supplierCounts.map(({ supplier, count }) => (
                            <label
                                key={supplier}
                                className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded"
                            >
                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={filterState.selectedSuppliers.includes(supplier)}
                                        onChange={() => handleSupplierToggle(supplier)}
                                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <span className="text-sm text-gray-700">{supplier}</span>
                                </div>
                                <span className="text-xs text-gray-500">({count})</span>
                            </label>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
