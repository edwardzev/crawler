"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Menu, X, ShoppingBag } from "lucide-react";
import { cn } from "@/lib/utils";
import { Product } from "@/lib/types";

export function Header() {
    const [query, setQuery] = useState("");
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const router = useRouter();

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            router.push(`/search?q=${encodeURIComponent(query)}`);
            setIsMenuOpen(false);
        }
    };

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
            <div className="container mx-auto flex h-16 items-center px-4">
                 <Link href="/" className="mr-6 flex items-center space-x-2">
                    <ShoppingBag className="h-6 w-6 text-blue-600" />
                    <span className="text-xl font-bold">קטלוג ספקים</span>
                 </Link>
                 
                 {/* Desktop Search */}
                 <div className="hidden flex-1 md:flex md:justify-center">
                    <form onSubmit={handleSearch} className="relative w-full max-w-lg">
                        <input
                            type="text" 
                            placeholder="חפש מוצרים..."
                            className="w-full rounded-full border border-gray-300 bg-gray-50 py-2 pl-4 pr-10 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button type="submit" className="absolute left-3 top-2.5 text-gray-400 hover:text-blue-600">
                             <Search className="h-5 w-5" />
                        </button>
                    </form>
                 </div>

                {/* Mobile Menu Button */}
                <button className="md:hidden mr-auto" onClick={() => setIsMenuOpen(!isMenuOpen)}>
                    {isMenuOpen ? <X /> : <Menu />}
                </button>
            </div>
            
             {/* Mobile Search & Menu */}
             {isMenuOpen && (
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
                            <Link href="/" className="py-2" onClick={() => setIsMenuOpen(false)}>דף הבית</Link>
                            <Link href="/c/categories" className="py-2" onClick={() => setIsMenuOpen(false)}>כל הקטגוריות</Link>
                        </nav>
                 </div>
             )}
        </header>
    );
}
