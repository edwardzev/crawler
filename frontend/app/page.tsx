import { getCategoriesTree, getProducts } from "@/lib/data";
import { Header } from "@/components/Header";
import { CategoryCard } from "@/components/CategoryCard";
import { RotatingText } from "@/components/RotatingText";
import Link from "next/link";

export default async function Home() {
  const categories = await getCategoriesTree();
  const products = await getProducts();

  const supplierLogos = [
    { name: "Comfort", src: "/supplier_logo/comfort_logo.jpg" },
    { name: "Kraus", src: "/supplier_logo/kraus_logo.png" },
    { name: "Polo", src: "/supplier_logo/polo_logo.webp" },
    { name: "Wave", src: "/supplier_logo/wave_logo.png" },
    { name: "Zeus", src: "/supplier_logo/zeus_logo.png" },
  ];

  // Get top categories (by count)
  const topCategories = categories.children
    .sort((a, b) => b.count - a.count)
    .slice(0, 12);


  return (
    <main className="min-h-screen bg-gray-50 pb-20">
      <Header categories={categories} />

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white px-4 py-24 text-center">
        <div className="container relative z-10 mx-auto max-w-4xl">
          <h1 className="mb-6 text-5xl font-extrabold tracking-tight text-gray-900 md:text-6xl lg:text-7xl">
            קטלוג מוצרים מלא <br />
            <RotatingText />
          </h1>
          <p className="mx-auto mb-10 max-w-5xl text-xl text-gray-500">
            הדרך המהירה והמתקדמת ביותר למצוא, לעצב ולהזמין מוצרי קד"מ.
            <br className="hidden md:inline" />
          </p>



          <div className="flex justify-center gap-12 text-gray-400 border-t border-gray-100 pt-8 mt-8 max-w-lg mx-auto">
            <div className="text-center">
              <span className="block text-3xl font-bold text-gray-900">{products.length}</span>
              <span className="text-sm">מוצרים בקטלוג</span>
            </div>
            <div className="h-10 w-px bg-gray-200" />
            <div className="text-center">
              <span className="block text-3xl font-bold text-gray-900">{new Set(products.map(p => p.supplier)).size}</span>
              <span className="text-sm">ספקים</span>
            </div>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 h-64 w-64 rounded-full bg-blue-50 blur-3xl opacity-60" />
        <div className="absolute bottom-0 left-0 -ml-20 h-64 w-64 rounded-full bg-purple-50 blur-3xl opacity-60" />
      </section>

      {/* Supplier Logos */}
      <section className="bg-white">
        <div className="container mx-auto px-4 py-10">
          <div className="text-right">
            <p className="text-sm font-semibold text-gray-500">ספקים</p>
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-8">
            {supplierLogos.map((logo) => (
              <Link
                key={logo.name}
                href={`/s/${logo.name.toLowerCase()}`}
                className="flex h-14 items-center justify-center rounded-lg border border-gray-100 bg-gray-50 px-6 shadow-sm transition-all hover:shadow-md hover:-translate-y-1 hover:border-blue-200"
              >
                <img
                  src={logo.src}
                  alt={`${logo.name} logo`}
                  className="h-8 w-auto object-contain opacity-80 hover:opacity-100 transition-opacity"
                  loading="lazy"
                />
              </Link>
            ))}
          </div>
        </div>
      </section>

      <div className="container mx-auto px-4 -mt-8">
        <div className="mb-8">
          <div className="mb-6 flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center">
            <h2 className="text-2xl font-bold text-gray-900">קטגוריות מובילות</h2>

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
