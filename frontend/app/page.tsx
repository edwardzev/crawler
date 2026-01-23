import { getCategoriesTree, getProducts } from "@/lib/data";
import { Header } from "@/components/Header";
import { CategoryCard } from "@/components/CategoryCard";
import Link from "next/link";
import { Product } from "@/lib/types";

export default async function Home() {
  const categories = await getCategoriesTree();
  const products = await getProducts();

  // Get top categories (by count)
  const topCategories = categories.children
    .sort((a, b) => b.count - a.count)
    .slice(0, 12);

  // Helper to find image for category
  const getCategoryImage = (catSlug: string) => {
    // Find a product that starts with this category slug
    const product = products.find(p => p.category_slug_path && p.category_slug_path.includes(catSlug) && p.image_main);
    return product?.image_main;
  }

  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      <Header />

      {/* Hero Section */}
      <section className="bg-blue-600 px-4 py-20 text-center text-white">
        <h1 className="mb-4 text-4xl font-bold md:text-5xl">קטלוג מוצרים לספקים</h1>
        <p className="mb-8 text-xl text-blue-100">חיפוש מהיר ונוח בכל הקטגוריות</p>
      </section>

      <div className="container mx-auto px-4 -mt-8">
        <div className="mb-8">
          <h2 className="mb-6 text-2xl font-bold text-gray-900">קטגוריות מובילות</h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4">
            {topCategories.map((cat) => (
              <CategoryCard
                key={cat.slug}
                category={cat}
                imageUrl={getCategoryImage(cat.slug)}
              />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
