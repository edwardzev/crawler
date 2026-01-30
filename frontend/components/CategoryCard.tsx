import { CategoryNode } from "@/lib/types";

interface CategoryCardProps {
    category: CategoryNode;
    imageUrl?: string;
}

export function CategoryCard({ category }: CategoryCardProps) {
    // Pick a 3D product icon based on keyword matching
    // Map major categories to 3D abstract icons
    const getProductIcon = (name: string) => {
        const text = name.trim();

        // Explicit mapping for major categories
        const categoryMap: Record<string, string> = {
            'כלי כתיבה ומוצרי נייר': '/abstract/blue-pen.png',
            'יודאיקה ומתנות': '/abstract/cyan-umbrella.png', // Gifts/Leisure
            'בקבוקים ושתייה': '/abstract/green-bottle.png',
            'פנאי, טיולים ובית': '/abstract/cyan-umbrella.png', // Leisure/Outdoors
            'תיקים וארנקים': '/abstract/purple-bag.png',
            'גאדג\'טים וטכנולוגיה': '/abstract/orange-notebook.png', // Tech/Office
            'ביגוד וטקסטיל': '/abstract/purple-bag.png', // Fashion/Textile
            'כלי עבודה ושימוש': '/abstract/green-bottle.png', // Tools (utility)
            'UNCLASSIFIED': '/abstract/cyan-umbrella.png'
        };

        if (categoryMap[text]) return categoryMap[text];

        // Keyword fallback for subcategories or others
        const lower = text.toLowerCase();
        if (lower.includes('עט') || lower.includes('כתיבה')) return '/abstract/blue-pen.png';
        if (lower.includes('תיק')) return '/abstract/purple-bag.png';
        if (lower.includes('בקבוק') || lower.includes('שתייה')) return '/abstract/green-bottle.png';
        if (lower.includes('מחברת') || lower.includes('נייר')) return '/abstract/orange-notebook.png';

        // Hash fallback
        const icons = ['blue-pen', 'purple-bag', 'green-bottle', 'orange-notebook', 'cyan-umbrella'];
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            hash = text.charCodeAt(i) + ((hash << 5) - hash);
        }
        const index = Math.abs(hash) % icons.length;
        return `/abstract/${icons[index]}.png`;
    };

    const iconUrl = getProductIcon(category.name);
    const href = `/c/${encodeURIComponent(category.slug || "")}`;

    return (
        <a
            href={href}
            aria-label={`קטגוריה: ${category.name}`}
            className="group flex flex-col overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:border-blue-100 cursor-pointer"
        >
            <div className="aspect-square w-full overflow-hidden bg-slate-900 relative">
                <img
                    src={iconUrl}
                    alt={category.name}
                    className="h-full w-full object-contain p-8 transition-all duration-500 group-hover:scale-110 group-hover:brightness-125 pointer-events-none"
                    loading="lazy"
                />

                {/* Modern Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-80 pointer-events-none" />
                <div className="absolute bottom-4 right-4 text-white">
                    <h3 className="text-xl font-bold">{category.name}</h3>
                    <p className="text-sm opacity-90">{category.count} מוצרים</p>
                </div>
            </div>
        </a>
    );
}
