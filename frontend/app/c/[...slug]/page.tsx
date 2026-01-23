import { getCategoriesTree, getFlatCategories, getProducts } from "@/lib/data";
import { Sidebar } from "@/components/Sidebar";
import { ProductGrid } from "@/components/ProductGrid";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Header } from "@/components/Header";
import { WhatsAppButton } from "@/components/WhatsAppButton";
import { Metadata } from "next";

export async function generateStaticParams() {
    // Generate params for all categories
    const flatCats = await getFlatCategories();

    // Params expects { slug: ['cat', 'subcat'] }
    // Our flat list has slug_path array.
    return flatCats.map((cat) => ({
        slug: cat.slug_path,
    }));
}

type Props = {
    params: Promise<{ slug: string[] }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const { slug } = await params;
    const pathSlug = slug[slug.length - 1];
    // We would need to look up the name.
    // For now, let's just capitalize slug or find it via data.
    return {
        title: `${pathSlug} | קטלוג ספקים`,
    };
}

export default async function CategoryPage({ params }: Props) {
    const { slug } = await params;
    // Decode slug segments to handle Hebrew/special chars correctly
    const decodedSlug = slug.map(s => decodeURIComponent(s));

    const categoriesTree = await getCategoriesTree();
    const products = await getProducts();
    const flatCategories = await getFlatCategories();

    // Find the current category based on the *full* slug path.
    const currentCategory = flatCategories.find(c =>
        c.slug_path.length === decodedSlug.length &&
        c.slug_path.every((s, i) => s === decodedSlug[i])
    );

    const categoryName = currentCategory ? currentCategory.path[currentCategory.path.length - 1] : "קטגוריה";

    // Filter products
    const filteredProducts = products.filter(p => {
        if (p.category_slug_path.length < decodedSlug.length) return false;
        for (let i = 0; i < decodedSlug.length; i++) {
            if (p.category_slug_path[i] !== decodedSlug[i]) return false;
        }
        return true;
    });

    // Breadcrumbs
    const breadcrumbs = [
        ...decodedSlug.map((s, i) => {
            // Reconstruct path up to i
            const partialPath = decodedSlug.slice(0, i + 1);
            // Find name for this segment? 
            // We can find the category for this partial path
            const cat = flatCategories.find(c =>
                c.slug_path.length === partialPath.length &&
                c.slug_path.every((val, idx) => val === partialPath[idx])
            );
            return {
                label: cat ? cat.path[cat.path.length - 1] : s,
                href: `/c/${partialPath.join('/')}`
            };
        })
    ];

    return (
        <div className="min-h-screen bg-gray-50">
            <Header />

            <div className="container mx-auto py-8 px-4">
                <div className="mb-6">
                    <Breadcrumbs items={breadcrumbs} />
                </div>

                <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">{categoryName}</h1>
                        <p className="mt-2 text-gray-500">{filteredProducts.length} מוצרים בקטגוריה</p>
                    </div>
                    <div className="mt-4 md:mt-0">
                        <WhatsAppButton categoryName={categoryName} label="שאל על קטגוריה זו" />
                    </div>
                </div>

                <div className="flex flex-col md:flex-row gap-8">
                    <div className="hidden md:block">
                        <Sidebar tree={categoriesTree} />
                    </div>

                    <div className="flex-1">
                        <ProductGrid products={filteredProducts} />
                    </div>
                </div>
            </div>
        </div>
    );
}
