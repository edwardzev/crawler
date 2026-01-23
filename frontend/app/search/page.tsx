"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { Header } from "@/components/Header";
import { ProductGrid } from "@/components/ProductGrid";
import { searchProducts } from "@/lib/search";
import { Product } from "@/lib/types";
import { Loader2 } from "lucide-react";

function SearchResults() {
    const searchParams = useSearchParams();
    const query = searchParams.get("q") || "";
    const [results, setResults] = useState<Product[]>([]);
    const [loading, setLoading] = useState(false);
    const [allProducts, setAllProducts] = useState<Product[]>([]);

    useEffect(() => {
        // Fetch data once
        setLoading(true);
        fetch("/data/products.frontend.json")
            .then(res => res.json())
            .then(data => {
                setAllProducts(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    useEffect(() => {
        if (!query || allProducts.length === 0) {
            setResults([]);
            return;
        }

        const hits = searchProducts(allProducts, query);
        setResults(hits);

    }, [query, allProducts]);

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="mb-6 text-2xl font-bold">תוצאות חיפוש: "{query}"</h1>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="animate-spin text-blue-600 h-10 w-10" />
                </div>
            ) : (
                <>
                    <p className="mb-4 text-gray-500">{results.length} תוצאות</p>
                    <ProductGrid products={results} />
                </>
            )}
        </div>
    );
}

export default function SearchPage() {
    return (
        <div className="min-h-screen bg-gray-50">
            <Header />
            <Suspense fallback={<div className="container mx-auto px-4 py-8"><div className="flex justify-center py-20"><Loader2 className="animate-spin text-blue-600 h-10 w-10" /></div></div>}>
                <SearchResults />
            </Suspense>
        </div>
    );
}
