import { getCategoriesTree, getProducts } from "@/lib/data";
import { Header } from "@/components/Header";
import { CategoryCard } from "@/components/CategoryCard";
import Link from "next/link";

export default async function Home() {
  const categories = await getCategoriesTree();
  const products = await getProducts();

  // Get top categories (by count)
  const topCategories = categories.children
    .sort((a, b) => b.count - a.count)
    .slice(0, 12);


  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      <Header />

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-slate-950 px-4 py-24 text-white">
        {/* Mesh Gradient Overlay */}
        <div className="absolute inset-0 z-0 opacity-40">
          <div className="absolute -left-[10%] -top-[10%] h-[50%] w-[50%] rounded-full bg-blue-600/30 blur-[120px]" />
          <div className="absolute -right-[10%] -bottom-[10%] h-[50%] w-[50%] rounded-full bg-purple-600/30 blur-[120px]" />
        </div>

        <div className="container relative z-10 mx-auto grid items-center gap-12 md:grid-cols-2">
          <div className="text-right">
            <h1 className="mb-6 text-5xl font-extrabold tracking-tight md:text-6xl lg:text-7xl">
              קטלוג מוצרים <br />
              <span className="bg-gradient-to-l from-blue-400 to-purple-400 bg-clip-text text-transparent">
                לספקים מובילים
              </span>
            </h1>
            <p className="mb-10 text-xl text-slate-400 max-w-lg mr-0">
              הדרך המהירה והמתקדמת ביותר למצוא, לעצב ולהזמין מוצרי קד"מ בהתאמה אישית.
            </p>
            <div className="flex justify-end gap-6 mb-8">
              <div className="text-center">
                <span className="block text-3xl font-bold text-white">{products.length}</span>
                <span className="text-sm text-slate-400">מוצרים בקטלוג</span>
              </div>
              <div className="h-10 w-px bg-slate-800" />
              <div className="text-center">
                <span className="block text-3xl font-bold text-white">{new Set(products.map(p => p.supplier)).size}</span>
                <span className="text-sm text-slate-400">ספקים מובילים</span>
              </div>
            </div>

            <div className="flex justify-end gap-4">
              <Link href="/c/categories" className="rounded-full bg-white px-8 py-3 font-semibold text-slate-950 transition-transform hover:scale-105 active:scale-95">
                צפה בכל הקטגוריות
              </Link>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="relative aspect-square">
              <div className="absolute inset-0 rounded-full bg-blue-500/10 blur-3xl" />
              <img
                src="/hero-visual.png"
                alt="Product Catalog"
                className="relative z-10 h-full w-full object-contain animate-float"
              />
            </div>
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4 -mt-8">
        <div className="mb-8">
          <div className="mb-6 flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center">
            <h2 className="text-2xl font-bold text-gray-900">קטגוריות מובילות</h2>
            <p className="text-sm text-gray-500">סה״כ מוצרים: {products.length}</p>
          </div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4">
            {topCategories.map((cat) => (
              <CategoryCard
                key={cat.slug}
                category={cat}
                imageUrl={undefined}
              />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
