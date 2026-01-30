import { getProducts, buildCategoryTreeFromProducts } from "@/lib/data";
import { Header } from "@/components/Header";
import { ProductGrid } from "@/components/ProductGrid";
import { CategoryCard } from "@/components/CategoryCard";
import { Metadata } from "next";

// Helper to get logo for supplier
const getSupplierLogo = (supplier: string) => {
    const map: Record<string, string> = {
        'comfort': '/supplier_logo/comfort_logo.jpg',
        'kraus': '/supplier_logo/kraus_logo.png',
        'polo': '/supplier_logo/polo_logo.webp',
        'wave': '/supplier_logo/wave_logo.png',
        'zeus': '/supplier_logo/zeus_logo.png'
    };
    // normalize
    const key = supplier.toLowerCase().replace(/['"\s-]/g, '');
    // try direct match or fuzzy
    for (const k in map) {
        if (key.includes(k) || k.includes(key)) return map[k];
    }
    return null;
};

type Props = {
    params: Promise<{ supplier: string }>;
};

export async function generateStaticParams() {
    const products = await getProducts();
    const suppliers = new Set(products.map(p => p.supplier_slug).filter(Boolean));
    return Array.from(suppliers).map(slug => ({
        supplier: slug as string
    }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const { supplier } = await params;
    const products = await getProducts();
    // Normalize logic or finding actual display name
    // We can find one product with this slug
    const representative = products.find(p => p.supplier_slug === supplier);
    const displayName = representative?.supplier || supplier;

    return {
        title: `קטלוג ${displayName} | מגוון מוצרי ${displayName}`,
        description: `קטלוג המוצרים המלא של ${displayName}. כל המוצרים, המחירים והאפשרויות במקום אחד.`,
    };
}

export default async function SupplierPage({ params }: Props) {
    const { supplier } = await params;
    const allProducts = await getProducts();

    // 1. Filter products by supplier slug
    const supplierProducts = allProducts.filter(p => p.supplier_slug === supplier);

    if (supplierProducts.length === 0) {
        return <div className="p-10 text-center">ספק לא נמצא</div>;
    }

    // 2. Get display name
    const displayName = supplierProducts[0].supplier;
    const logoUrl = getSupplierLogo(displayName);

    // 3. Build category tree for THIS supplier only
    const categoryTree = buildCategoryTreeFromProducts(supplierProducts);

    // Sort categories by count
    const topCategories = (categoryTree.children || [])
        .sort((a, b) => b.count - a.count);

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <Header categories={categoryTree} />

            {/* Supplier Hero */}
            <section className="bg-white border-b border-gray-200">
                <div className="container mx-auto px-4 py-16 text-center">
                    {logoUrl && (
                        <div className="mb-6 flex justify-center">
                            <div className="h-24 w-auto p-4 rounded-xl border border-gray-100 shadow-sm bg-white inline-flex items-center justify-center">
                                {/* eslint-disable-next-line @next/next/no-img-element */}
                                <img
                                    src={logoUrl}
                                    alt={displayName}
                                    className="max-h-full max-w-full object-contain"
                                />
                            </div>
                        </div>
                    )}

                    <h1 className="text-4xl font-extrabold text-gray-900 mb-4">
                        קטלוג {displayName}
                    </h1>
                    <p className="text-xl text-gray-500 max-w-2xl mx-auto">
                        {supplierProducts.length} מוצרים זמינים בקטלוג
                    </p>
                </div>
            </section>

            {/* Categories Grid */}
            <section className="container mx-auto px-4 py-12">
                <div className="mb-8 flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900">קטגוריות ב-{displayName}</h2>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                    {topCategories.map((cat) => (
                        <CategoryCard
                            key={cat.slug}
                            category={cat}
                        />
                    ))}
                </div>
            </section>

            {/* Products (Recent / Featured for this supplier) */}
            <section className="container mx-auto px-4 py-12 border-t border-gray-200">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900">כל המוצרים של {displayName}</h2>
                </div>
                <ProductGrid products={supplierProducts} />
            </section>
        </div>
    );
}
