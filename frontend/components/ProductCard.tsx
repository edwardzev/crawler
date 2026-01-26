import Link from "next/link";
import { Product } from "@/lib/types";
import { WhatsAppButton } from "./WhatsAppButton";

interface ProductCardProps {
    product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
    return (
        <div className="group flex flex-col overflow-hidden rounded-lg border bg-white shadow-sm transition-shadow hover:shadow-md">
            <Link href={`/p/${product.supplier_slug}/${product.sku_clean}/${product.slug}`} className="aspect-square w-full overflow-hidden bg-gray-100 relative">
                {product.image_main ? (
                    <img
                        src={product.image_main}
                        alt={product.title}
                        className="h-full w-full object-contain object-center transition-transform group-hover:scale-105"
                        loading="lazy"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center text-gray-400">
                        תמונה חסרה
                    </div>
                )}
            </Link>
            <div className="flex flex-1 flex-col p-4">
                <div className="mb-2">
                    <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                        {product.supplier}
                    </span>
                </div>
                <Link href={`/p/${product.supplier_slug}/${product.sku_clean}/${product.slug}`} className="mb-2 block flex-1">
                    <h3 className="line-clamp-2 text-lg font-medium text-gray-900 group-hover:text-blue-600">
                        {product.title}
                    </h3>
                </Link>
                <div className="mb-4 text-sm text-gray-500">
                    מק"ט: {product.sku}
                </div>
                <div className="mb-4 font-bold text-gray-900">
                    {product.price ? `₪${product.price.toLocaleString()}` : "מחיר לפי דרישה"}
                </div>
                <div className="mt-auto">
                    <WhatsAppButton product={product} size="sm" className="w-full" />
                </div>
            </div>
        </div>
    );
}
