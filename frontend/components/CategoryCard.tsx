import { CategoryNode } from "@/lib/types";

interface CategoryCardProps {
    category: CategoryNode;
    imageUrl?: string;
}

export function CategoryCard({ category }: CategoryCardProps) {
    // Pick a 3D product icon based on keyword matching
    const getProductIcon = (name: string) => {
        const text = name.toLowerCase();
        if (text.includes('עט') || text.includes('כתיבה') || text.includes('pen')) return '/abstract/blue-pen.png';
        if (text.includes('תיק') || text.includes('bag')) return '/abstract/purple-bag.png';
        if (text.includes('בקבוק') || text.includes('bottle') || text.includes('שתייה')) return '/abstract/green-bottle.png';
        if (text.includes('מחברת') || text.includes('מכתביות') || text.includes('notebook')) return '/abstract/orange-notebook.png';
        if (text.includes('קיץ') || text.includes('ים') || text.includes('umbrella') || text.includes('מניפות')) return '/abstract/cyan-umbrella.png';

        // Fallback to a consistent hash-based abstract icon if no product match
        const icons = ['blue-pen', 'purple-bag', 'green-bottle', 'orange-notebook', 'cyan-umbrella'];
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
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
