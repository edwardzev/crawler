import { CategoryNode } from "@/lib/types";
import {
    PenTool,
    Gift,
    GlassWater,
    Tent,
    Briefcase,
    Zap,
    Shirt,
    Hammer,
    Box,
    LucideIcon,
    ChevronLeft
} from "lucide-react";
import Link from "next/link";

interface CategoryCardProps {
    category: CategoryNode;
    imageUrl?: string;
}

export function CategoryCard({ category }: CategoryCardProps) {
    const getIcon = (name: string): LucideIcon => {
        const text = name.trim();

        const categoryMap: Record<string, LucideIcon> = {
            'כלי כתיבה ומוצרי נייר': PenTool,
            'יודאיקה ומתנות': Gift,
            'בקבוקים ושתייה': GlassWater,
            'פנאי, טיולים ובית': Tent,
            'תיקים וארנקים': Briefcase,
            'גאדג\'טים וטכנולוגיה': Zap,
            'ביגוד וטקסטיל': Shirt,
            'כלי עבודה ושימוש': Hammer,
        };

        if (categoryMap[text]) return categoryMap[text];

        // Keyword fallback
        const lower = text.toLowerCase();
        if (lower.includes('עט') || lower.includes('כתיבה')) return PenTool;
        if (lower.includes('תיק')) return Briefcase;
        if (lower.includes('בקבוק') || lower.includes('שתייה')) return GlassWater;
        if (lower.includes('מחברת') || lower.includes('נייר')) return PenTool;
        if (lower.includes('ביגוד') || lower.includes('חולצ')) return Shirt;
        if (lower.includes('מחשב') || lower.includes('גאד')) return Zap;

        return Box;
    };

    const Icon = getIcon(category.name);
    const href = `/c/${encodeURIComponent(category.slug || "")}`;
    const hasChildren = category.children && category.children.length > 0;

    return (
        <div
            dir="rtl"
            className="group relative flex flex-col p-6 rounded-2xl border border-gray-100 bg-white shadow-sm transition-all duration-300 hover:shadow-md hover:border-blue-200 hover:-translate-y-1 z-10 hover:z-20"
        >
            <Link href={href} className="flex flex-col items-center justify-center w-full h-full">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 transition-colors group-hover:bg-blue-600 group-hover:text-white">
                    <Icon strokeWidth={1.5} className="h-8 w-8" />
                </div>
                <h3 className="text-lg font-bold text-gray-900 text-center mb-1">{category.name}</h3>
                <p className="text-sm text-gray-500">{category.count} מוצרים</p>
            </Link>

            {/* Mega Menu Dropdown */}
            {hasChildren && (
                <div className="absolute right-0 top-[90%] left-0 pt-4 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 ease-out transform translate-y-2 group-hover:translate-y-0 z-50">
                    <div className="bg-white rounded-xl shadow-xl border border-gray-100 p-3 overflow-hidden">
                        <ul className="space-y-1">
                            {category.children!.slice(0, 6).map((child) => (
                                <li key={child.slug}>
                                    <Link
                                        href={`/c/${encodeURIComponent(category.slug)}/${encodeURIComponent(child.slug)}`}
                                        className="flex items-center justify-between px-3 py-2 rounded-lg text-sm text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                                    >
                                        <span className="truncate">{child.name}</span>
                                        <ChevronLeft className="h-3 w-3 opacity-0 group-hover/link:opacity-100" />
                                    </Link>
                                </li>
                            ))}
                            {category.children!.length > 6 && (
                                <li className="pt-2 border-t border-gray-50 mt-1">
                                    <Link
                                        href={href}
                                        className="text-xs text-center block text-blue-500 hover:underline font-medium"
                                    >
                                        עוד {category.children!.length - 6} קטגוריות...
                                    </Link>
                                </li>
                            )}
                        </ul>
                    </div>
                </div>
            )}
        </div>
    );
}
