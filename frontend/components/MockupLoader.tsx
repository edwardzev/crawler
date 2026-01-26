"use client";

import dynamic from 'next/dynamic';
import React from 'react';
import { Product } from "@/lib/types";

// Client Component Wrapper
const MockupEditor = dynamic(() => import('@/components/MockupEditor'), {
    loading: () => (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 text-white">
            <div className="animate-pulse text-xl font-bold">טוען עורך...</div>
        </div>
    ),
    ssr: false
});

interface Props {
    product: Product;
}

export default function MockupLoader({ product }: Props) {
    const [isOpen, setIsOpen] = React.useState(false);

    return (
        <>
            {/* Trigger Button */}
            <div className="mt-8 flex justify-center">
                <button
                    onClick={() => setIsOpen(true)}
                    className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-4 text-lg font-bold text-white shadow-lg transition-transform hover:scale-105 hover:shadow-xl active:scale-95"
                >
                    <span className="text-2xl">🎨</span>
                    צור הדמיה עם לוגו
                </button>
            </div>

            {/* Modal Overlay */}
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
                    <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-2xl animate-in zoom-in-95 duration-200">
                        <button
                            onClick={() => setIsOpen(false)}
                            className="absolute right-4 top-4 z-10 rounded-full bg-gray-100 p-2 text-gray-500 hover:bg-gray-200 transition"
                        >
                            ✕
                        </button>

                        <div className="p-1">
                            <MockupEditor product={product} onClose={() => setIsOpen(false)} />
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
