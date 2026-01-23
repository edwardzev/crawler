import Link from "next/link";
import { CategoryNode } from "@/lib/types";

interface CategoryCardProps {
    category: CategoryNode;
    imageUrl?: string;
}

export function CategoryCard({ category, imageUrl }: CategoryCardProps) {
    return (
        <Link
            href={`/c/${category.slug}`}
            className="group flex flex-col overflow-hidden rounded-lg border bg-white shadow-sm transition-shadow hover:shadow-md"
        >
            <div className="aspect-square w-full overflow-hidden bg-gray-100 relative">
                {imageUrl ? (
                    <img
                        src={imageUrl}
                        alt={category.name}
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        loading="lazy"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center text-gray-400 bg-gray-50">
                        <span className="text-4xl text-gray-300">📁</span>
                    </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60" />
                <div className="absolute bottom-4 right-4 text-white">
                    <h3 className="text-xl font-bold">{category.name}</h3>
                    <p className="text-sm opacity-90">{category.count} מוצרים</p>
                </div>
            </div>
        </Link>
    );
}
