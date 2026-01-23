import { getProducts } from "@/lib/data";
import { Header } from "@/components/Header";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { WhatsAppButton } from "@/components/WhatsAppButton";
import { Metadata } from "next";
import { ChevronRight } from "lucide-react";
import { ImageGallery } from "@/components/ImageGallery";
import Link from "next/link";

type Props = {
    params: Promise<{ id: string; slug: string }>;
};

export async function generateStaticParams() {
    const products = await getProducts();
    return products.map((product) => ({
        id: String(product.id),
        slug: product.slug, // ensure slug is url encoded if needed, but nextjs handles it
    }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const { id } = await params;
    const products = await getProducts();
    const product = products.find((p) => String(p.id) === id);

    if (!product) {
        return { title: "Product Not Found" };
    }

    return {
        title: `${product.title} | ${product.supplier} | קטלוג`,
        description: `מק"ט: ${product.sku}. ${product.description || ""}`.slice(0, 160),
        openGraph: {
            images: product.image_main ? [product.image_main] : [],
        },
    };
}

export default async function ProductPage({ params }: Props) {
    const { id } = await params;
    const products = await getProducts();
    const product = products.find((p) => String(p.id) === id);

    if (!product) {
        return <div className="p-10 text-center">מוצר לא נמצא</div>;
    }

    // Build breadcrumbs from category path
    // We have 'category_slug_path' and 'category_path'.
    // We need to zip them.
    const breadcrumbs = product.category_path.map((name, index) => {
        // Reconstruct slug path up to index
        const slugPath = product.category_slug_path.slice(0, index + 1).join("/");
        return { label: name, href: `/c/${slugPath}` };
    });

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <Header />

            <div className="container mx-auto px-4 py-8">
                <div className="mb-6">
                    <Breadcrumbs items={breadcrumbs} />
                </div>

                <div className="overflow-hidden rounded-xl bg-white shadow-lg">
                    <div className="grid md:grid-cols-2">

                        {/* Gallery Section */}
                        <div className="bg-gray-100 p-8">
                            <ImageGallery images={product.images} title={product.title} />
                        </div>

                        {/* Details Section */}
                        <div className="p-8">
                            <div className="mb-4">
                                <span className="inline-block rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
                                    {product.supplier}
                                </span>
                            </div>

                            <h1 className="mb-4 text-3xl font-bold text-gray-900">{product.title}</h1>

                            <div className="mb-6 text-lg text-gray-600">
                                <span className="font-bold">מק"ט:</span> {product.sku}
                            </div>

                            <div className="mb-6 text-2xl font-bold text-blue-600">
                                {product.price ? `₪${product.price.toLocaleString()}` : "מחיר לפי דרישה"}
                            </div>

                            {product.description && (
                                <div className="mb-8 prose prose-blue text-gray-600">
                                    <h3 className="text-lg font-bold text-gray-800 mb-2">תיאור</h3>
                                    <p>{product.description}</p>
                                </div>
                            )}

                            {/* Properties Table */}
                            {product.properties && Object.keys(product.properties).length > 0 && (
                                <div className="mb-8">
                                    <h3 className="text-lg font-bold text-gray-800 mb-2">מאפיינים</h3>
                                    <div className="overflow-hidden rounded-lg border border-gray-200">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <tbody className="divide-y divide-gray-200 bg-white">
                                                {Object.entries(product.properties).map(([key, value]) => (
                                                    <tr key={key}>
                                                        <td className="whitespace-nowrap bg-gray-50 px-4 py-2 text-sm font-medium text-gray-500">{key}</td>
                                                        <td className="whitespace-nowrap px-4 py-2 text-sm text-gray-900">{String(value)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex flex-col gap-4 border-t pt-8">
                                <WhatsAppButton product={product} size="lg" className="w-full text-lg" />

                                {product.url && (
                                    <a href={product.url} target="_blank" rel="noopener noreferrer" className="text-center text-sm text-gray-400 hover:text-gray-600 hover:underline">
                                        למקור אצל הספק
                                    </a>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
