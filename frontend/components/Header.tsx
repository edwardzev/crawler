"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Menu, X, ShoppingBag, ChevronDown, Home } from "lucide-react";
import { cn } from "@/lib/utils";
import { Product, CategoryNode } from "@/lib/types";

interface HeaderProps {
    categories?: CategoryNode;
}

const supplierLogos = [
    { name: "Comfort", src: "/supplier_logo/comfort_logo.jpg" },
    { name: "Kraus", src: "/supplier_logo/kraus_logo.png" },
    { name: "Polo", src: "/supplier_logo/polo_logo.webp" },
    { name: "Wave", src: "/supplier_logo/wave_logo.png" },
    { name: "Zeus", src: "/supplier_logo/zeus_logo.png" },
];

export function Header({ categories }: HeaderProps) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<Product[]>([]);

    // Search dropdown state
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    // Mobile menu state
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    // Mega menu state
    const [isMegaMenuOpen, setIsMegaMenuOpen] = useState(false);
    const megaMenuTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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

    const handleMouseEnter = () => {
        if (megaMenuTimeoutRef.current) {
            clearTimeout(megaMenuTimeoutRef.current);
        }
        setIsMegaMenuOpen(true);
    };

    const handleMouseLeave = () => {
        megaMenuTimeoutRef.current = setTimeout(() => {
            setIsMegaMenuOpen(false);
        }, 150);
    };

    // Get top-level categories for the mega menu
    const menuCategories = categories?.children || [];
    // Sort by count descending for better relevance in menu
    const sortedMenuCategories = [...menuCategories].sort((a, b) => b.count - a.count);

    return (
        <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white shadow-sm">
            <div className="container mx-auto flex h-16 items-center px-4 justify-between">
                <div className="flex items-center">
                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center space-x-6 mr-0">
                        {/* Home Icon */}
                        <Link
                            href="/"
                            className="flex items-center justify-center p-2 rounded-full text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                            aria-label="דף הבית"
                        >
                            <Home className="h-5 w-5" />
                        </Link>

                        {/* Mega Menu Trigger */}
                        <div
                            className="relative"
                            onMouseEnter={handleMouseEnter}
                            onMouseLeave={handleMouseLeave}
                        >
                            <button
                                className={cn(
                                    "flex items-center gap-2 text-sm font-bold px-5 py-2.5 rounded-full transition-all duration-200 shadow-sm",
                                    isMegaMenuOpen
                                        ? "bg-blue-700 text-white shadow-md ring-2 ring-blue-100"
                                        : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md hover:-translate-y-0.5"
                                )}
                            >
                                <Menu className="h-4 w-4" />
                                קטלוג מוצרים
                                <ChevronDown className={cn("h-4 w-4 transition-transform opacity-80", isMegaMenuOpen && "rotate-180")} />
                            </button>

                            {/* Mega Menu Dropdown */}
                            {isMegaMenuOpen && (
                                <div className="absolute top-full right-0 w-[800px] bg-white shadow-xl rounded-b-xl border-t border-gray-100 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                                    <div className="flex">
                                        {/* Main Categories Columns */}
                                        <div className="flex-1 p-6 grid grid-cols-3 gap-6">
                                            {sortedMenuCategories.slice(0, 15).map((category) => (
                                                <div key={category.slug} className="group">
                                                    <Link
                                                        href={`/c/${category.slug}`}
                                                        className="font-bold text-gray-900 hover:text-blue-600 block mb-2"
                                                        onClick={() => setIsMegaMenuOpen(false)}
                                                    >
                                                        {category.name}
                                                    </Link>
                                                    {category.children && category.children.length > 0 && (
                                                        <ul className="space-y-1">
                                                            {category.children.slice(0, 4).map((sub) => (
                                                                <li key={sub.slug}>
                                                                    <Link
                                                                        href={`/c/${category.slug}/${sub.slug}`}
                                                                        className="text-sm text-gray-500 hover:text-blue-500 transition-colors block"
                                                                        onClick={() => setIsMegaMenuOpen(false)}
                                                                    >
                                                                        {sub.name}
                                                                    </Link>
                                                                </li>
                                                            ))}
                                                            {category.children.length > 4 && (
                                                                <li>
                                                                    <Link
                                                                        href={`/c/${category.slug}`}
                                                                        className="text-xs text-blue-500 hover:underline mt-1 block"
                                                                        onClick={() => setIsMegaMenuOpen(false)}
                                                                    >
                                                                        עוד {category.children.length - 4} קטגוריות...
                                                                    </Link>
                                                                </li>
                                                            )}
                                                        </ul>
                                                    )}
                                                </div>
                                            ))}
                                        </div>

                                        {/* Sidebar / CTA in Mega Menu */}
                                        <div className="w-64 bg-gray-50 p-6 flex flex-col justify-between border-r border-gray-100">
                                            <div>
                                                <h3 className="font-bold text-gray-900 mb-4 text-lg border-b pb-2">הספקים שלנו</h3>
                                                <div className="grid grid-cols-2 gap-4">
                                                    {supplierLogos.map((logo) => (
                                                        <Link
                                                            key={logo.name}
                                                            href={`/s/${logo.name.toLowerCase()}`}
                                                            className="flex items-center justify-center p-2 bg-white rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-all hover:-translate-y-0.5 h-16"
                                                        >
                                                            {/* eslint-disable-next-line @next/next/no-img-element */}
                                                            <img
                                                                src={logo.src}
                                                                alt={logo.name}
                                                                className="max-h-full max-w-full object-contain"
                                                            />
                                                        </Link>
                                                    ))}
                                                </div>

                                                <div className="mt-8 pt-4 border-t border-gray-200">
                                                    <Link
                                                        href="/c/categories"
                                                        className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center justify-center gap-1 group"
                                                        onClick={() => setIsMegaMenuOpen(false)}
                                                    >
                                                        כל הקטגוריות
                                                        <span className="group-hover:translate-x-1 transition-transform rtl:rotate-180">←</span>
                                                    </Link>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </nav>
                </div>

                {/* Desktop Search */}
                <div className="hidden flex-1 md:flex md:justify-center md:max-w-2xl relative mx-4">
                    <form onSubmit={handleSearch} className="relative w-full z-40">
                        <input
                            type="text"
                            placeholder="חפש מוצרים..."
                            className="w-full rounded-full border border-gray-300 bg-gray-50 py-2 pl-4 pr-10 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors shadow-sm"
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
                                className="fixed inset-0 z-30"
                                onClick={() => setIsSearchOpen(false)}
                            />
                            <div className="absolute top-full mt-2 w-full bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden z-50">
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
                <button className="md:hidden mr-auto text-gray-600" onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}>
                    {isMobileMenuOpen ? <X /> : <Menu />}
                </button>
            </div>

            {/* Mobile Search & Menu */}
            {isMobileMenuOpen && (
                <div className="border-t bg-white p-4 md:hidden animate-in slide-in-from-top-2">
                    <form onSubmit={handleSearch} className="mb-4">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="חפש מוצרים..."
                                className="w-full rounded-md border border-gray-300 p-2 pr-10"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                            />
                            <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                        </div>
                    </form>
                    <nav className="flex flex-col space-y-1">
                        <Link href="/" className="py-2 px-2 rounded hover:bg-gray-50 font-medium" onClick={() => setIsMobileMenuOpen(false)}>ראשי</Link>
                        <Link href="/c/categories" className="py-2 px-2 rounded hover:bg-gray-50 font-medium text-blue-600" onClick={() => setIsMobileMenuOpen(false)}>קטלוג מוצרים</Link>
                        <Link href="/about" className="py-2 px-2 rounded hover:bg-gray-50 font-medium" onClick={() => setIsMobileMenuOpen(false)}>אודות</Link>
                        <Link href="/contact" className="py-2 px-2 rounded hover:bg-gray-50 font-medium" onClick={() => setIsMobileMenuOpen(false)}>צור קשר</Link>
                    </nav>
                </div>
            )}
        </header>
    );
}
