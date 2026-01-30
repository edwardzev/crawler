"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Menu, X, ShoppingBag } from "lucide-react";
import { cn } from "@/lib/utils";
import { Product } from "@/lib/types";

export function Header() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<Product[]>([]);

    // Search dropdown state
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    // Mobile menu state
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const router = useRouter();

    useEffect(() => {
        const timeoutId = setTimeout(async () => {
            if (query.length > 1) {
                try {
                    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    setResults(data);
                    setIsSearchOpen(true);
                } catch (e) {
                    console.error(e);
                }
            } else {
                setResults([]);
                setIsSearchOpen(false);
            }
        }, 300); // 300ms debounce

        return () => clearTimeout(timeoutId);
    }, [query]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            router.push(`/search?q=${encodeURIComponent(query)}`);
            setIsSearchOpen(false);
            setIsMobileMenuOpen(false);
        }
    };

    return (
        <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white shadow-sm">
            <div className="container mx-auto flex h-16 items-center px-4">
                <Link href="/" className="mr-6 flex items-center space-x-2">
                    <ShoppingBag className="h-6 w-6 text-blue-600" />
                    <span className="text-xl font-bold text-gray-900">קטלוג ספקים</span>
                </Link>

                {/* Desktop Search */}
                <div className="hidden flex-1 md:flex md:justify-center relative">
                    <form onSubmit={handleSearch} className="relative w-full max-w-lg z-50">
                        <input
                            type="text"
                            placeholder="חפש מוצרים..."
                            className="w-full rounded-full border border-gray-300 bg-gray-100 py-2 pl-4 pr-10 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
                            value={query}
                            onChange={(e) => {
                                setQuery(e.target.value);
                                setIsSearchOpen(true);
                            }}
                            onFocus={() => setIsSearchOpen(true)}
                        />
                        <button type="submit" className="absolute left-3 top-2.5 text-gray-400 hover:text-blue-600">
                            <Search className="h-5 w-5" />
                        </button>
                    </form>

                    {/* Search Results Dropdown */}
                    {isSearchOpen && results.length > 0 && (
                        <>
                            <div
                                className="fixed inset-0 z-40"
                                onClick={() => setIsSearchOpen(false)}
                            />
                            <div className="absolute top-full mt-2 w-full max-w-lg bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden z-50">
                                <div className="p-2 text-right text-xs text-gray-500 border-b">
                                    {results.length} תוצאות חיפוש
                                </div>
                                {results.map((product) => (
                                    <Link
                                        key={product.id}
                                        href={`/p/${product.slug}`}
                                        className="flex items-center gap-4 p-3 hover:bg-gray-50 transition-colors border-b last:border-0"
                                        onClick={() => setIsSearchOpen(false)}
                                    >
                                        <div className="h-12 w-12 flex-shrink-0 bg-gray-100 rounded-md overflow-hidden">
                                            {/* eslint-disable-next-line @next/next/no-img-element */}
                                            <img
                                                src={product.image_main || '/placeholder.png'}
                                                alt={product.title}
                                                className="h-full w-full object-cover"
                                            />
                                        </div>
                                        <div className="flex-1 text-right">
                                            <div className="text-sm font-medium text-gray-900 truncate">{product.title}</div>
                                            <div className="text-xs text-gray-500 flex justify-between mt-1">
                                                <span>{product.sku}</span>
                                                {/* Optional: Add functionality to see similarity/price if needed */}
                                            </div>
                                        </div>
                                    </Link>
                                ))}
                                <div
                                    className="p-3 text-center text-sm text-blue-600 hover:bg-blue-50 cursor-pointer font-medium"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        handleSearch(e as any);
                                    }}
                                >
                                    ראה את כל התוצאות
                                </div>
                            </div>
                        </>
                    )}
                </div>

                {/* Mobile Menu Button */}
                <button className="md:hidden mr-auto" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                    {isMobileMenuOpen ? <X /> : <Menu />}
                </button>
            </div>

            {/* Mobile Search & Menu */}
            {isMobileMenuOpen && (
                <div className="border-t bg-white p-4 md:hidden">
                    <form onSubmit={handleSearch}>
                        <input
                            type="text"
                            placeholder="חפש מוצרים..."
                            className="w-full rounded-md border p-2 mb-4"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                    </form>
                    <nav className="flex flex-col space-y-2">
                        <Link href="/" className="py-2" onClick={() => setIsMobileMenuOpen(false)}>דף הבית</Link>
                        <Link href="/c/categories" className="py-2" onClick={() => setIsMobileMenuOpen(false)}>כל הקטגוריות</Link>
                    </nav>
                </div>
            )}
        </header>
    );
}
