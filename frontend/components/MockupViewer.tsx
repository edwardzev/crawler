"use client";

import dynamic from "next/dynamic";
import { Product } from "@/lib/types";

const MockupEditor = dynamic(() => import("@/components/MockupEditor"), {
    ssr: false,
    loading: () => <div className="h-64 animate-pulse bg-gray-200" />,
});

interface MockupViewerProps {
    product: Product;
    mockup: any;
}

export function MockupViewer({ product, mockup }: MockupViewerProps) {
    return <MockupEditor product={product} initialState={mockup} readOnly={true} />;
}
