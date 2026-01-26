import { getProducts } from "@/lib/data";
import fs from "fs/promises";
import path from "path";
import dynamic from "next/dynamic";
import { Header } from "@/components/Header";
import { Link } from "lucide-react";

// Server Component
// Dynamic Editor Import
const MockupEditor = dynamic(() => import("@/components/MockupEditor"), {
    ssr: false,
    loading: () => <div className="h-64 animate-pulse bg-gray-200" />
});

type Props = {
    params: Promise<{ id: string }>;
};

async function getMockup(id: string) {
    // In dev: read from local file
    // In prod: would read from DB
    try {
        const filePath = path.resolve(process.cwd(), `public/data/mockups/${id}.json`);
        const data = await fs.readFile(filePath, "utf-8");
        return JSON.parse(data);
    } catch {
        return null;
    }
}

export default async function MockupViewPage({ params }: Props) {
    const { id } = await params;
    const mockup = await getMockup(id);

    if (!mockup) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-800">הדמיה לא נמצאה</h1>
                    <p className="text-gray-500">ייתכן שהקישור שגוי או פג תוקף.</p>
                </div>
            </div>
        );
    }

    // Load Product Data
    const products = await getProducts();
    const product = products.find(p =>
        (p.catalog_id === mockup.catalog_id) ||
        (p.supplier_slug === mockup.supplier_slug && p.sku_clean === mockup.sku_clean)
    );

    if (!product) {
        return <div className="p-10 text-center">מוצר מקורי לא נמצא</div>;
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Header />

            <div className="container mx-auto px-4 py-8 max-w-4xl">
                <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-gray-100">
                    <div className="bg-blue-600 px-6 py-4 flex items-center justify-between text-white">
                        <h1 className="text-lg font-bold flex items-center gap-2">
                            הדמיה למוצר: {product.title}
                        </h1>
                        <span className="text-sm bg-blue-700 px-3 py-1 rounded-full">
                            {product.sku}
                        </span>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8 p-8">
                        <div>
                            <MockupEditor product={product} initialState={mockup} readOnly={true} />
                        </div>

                        <div className="flex flex-col justify-center gap-4">
                            <div className="bg-yellow-50 border-r-4 border-yellow-400 p-4">
                                <p className="text-sm text-yellow-800">
                                    <strong>שים לב:</strong> הדמיה זו ממחישה את מיקום הלוגו המשוער.
                                    גודל ומיקום סופיים ייקבעו בגרפיקה ממוחשבת לפני ייצור.
                                </p>
                            </div>

                            <div className="space-y-4">
                                <h3 className="font-bold text-gray-800">פרטי הדמיה</h3>
                                <ul className="text-sm text-gray-600 space-y-2">
                                    <li>תאריך יצירה: {new Date(mockup.createdAt).toLocaleString('he-IL')}</li>
                                    <li>מזהה הדמיה: <span className="font-mono bg-gray-100 px-1">{mockup.id}</span></li>
                                </ul>

                                <a
                                    href={`/p/${product.supplier_slug}/${product.sku_clean}/${product.slug}`}
                                    className="block text-center mt-6 text-blue-600 hover:underline font-medium"
                                >
                                    מעבר לעמוד מוצר מקורי &rarr;
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
