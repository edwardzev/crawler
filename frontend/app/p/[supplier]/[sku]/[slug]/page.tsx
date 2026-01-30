import { getProducts } from "@/lib/data";
import { Header } from "@/components/Header";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Metadata } from "next";
import { ChevronRight } from "lucide-react";
import { ImageGallery } from "@/components/ImageGallery";
import Link from "next/link";
import { OrderSummary } from "@/components/OrderSummary";

const baseUrl = (process.env.NEXT_PUBLIC_BASE_URL || "https://example.com").replace(/\/$/, "");

type Props = {
    params: Promise<{ supplier: string; sku: string; slug: string }>;
};

export async function generateStaticParams() {
    const products = await getProducts();
    // Path: /p/[supplier]/[sku]/[slug]
    // Filter out items without complete ID info (should be none post-migration)
    return products
        .filter(p => p.supplier_slug && p.sku_clean)
        .map((product) => ({
            supplier: String(product.supplier_slug),
            sku: String(product.sku_clean),
            slug: String(product.slug),
        }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const { supplier, sku } = await params;
    const products = await getProducts();

    // Find by composite key
    const product = products.find(
        (p) => p.supplier_slug === supplier && p.sku_clean === sku
    );

    if (!product) {
        return { title: "Product Not Found" };
    }

    const canonicalUrl = `${baseUrl}/p/${product.supplier_slug}/${product.sku_clean}/${product.slug}`;
    const description = `מק"ט: ${product.sku}. ${product.description || ""}`.slice(0, 160);

    return {
        title: `${product.title} | ${product.supplier} | קטלוג`,
        description,
        alternates: {
            canonical: canonicalUrl,
        },
        openGraph: {
            title: `${product.title} | ${product.supplier} | קטלוג`,
            description,
            url: canonicalUrl,
            images: product.image_main ? [product.image_main] : [],
        },
        twitter: {
            title: `${product.title} | ${product.supplier} | קטלוג`,
            description,
            images: product.image_main ? [product.image_main] : [],
        },
    };
}

export default async function ProductPage({ params }: Props) {
    const { supplier, sku } = await params;
    const products = await getProducts();

    // Find by composite key
    const product = products.find(
        (p) => p.supplier_slug === supplier && p.sku_clean === sku
    );

    if (!product) {
        return <div className="p-10 text-center">מוצר לא נמצא</div>;
    }

    const canonicalUrl = `${baseUrl}/p/${product.supplier_slug}/${product.sku_clean}/${product.slug}`;

    // Build breadcrumbs from category path
    // We have 'category_slug_path' and 'category_path'.
    // We need to zip them.
    const breadcrumbs = product.category_path.map((name, index) => {
        // Reconstruct slug path up to index
        const slugPath = product.category_slug_path.slice(0, index + 1).join("/");
        return { label: name, href: `/c/${slugPath}` };
    });

    const breadcrumbJsonLd = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        itemListElement: [
            {
                "@type": "ListItem",
                position: 1,
                name: "קטלוג",
                item: `${baseUrl}`
            },
            ...breadcrumbs.map((item, index) => ({
                "@type": "ListItem",
                position: index + 2,
                name: item.label,
                item: `${baseUrl}${item.href}`
            }))
        ]
    };

    const availability = product.availability?.toLowerCase().includes("out")
        ? "https://schema.org/OutOfStock"
        : "https://schema.org/InStock";

    const productJsonLd: Record<string, unknown> = {
        "@context": "https://schema.org",
        "@type": "Product",
        name: product.title,
        description: product.description || undefined,
        sku: product.sku_clean || product.sku || undefined,
        brand: product.supplier || undefined,
        image: product.images && product.images.length > 0 ? product.images : undefined,
        url: canonicalUrl,
    };

    if (product.price) {
        productJsonLd.offers = {
            "@type": "Offer",
            priceCurrency: product.currency || "ILS",
            price: product.price,
            availability,
            url: canonicalUrl,
        };
    }

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <Header />

            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
            />
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{ __html: JSON.stringify(productJsonLd) }}
            />

            <div className="container mx-auto px-4 py-8">
                <div className="mb-6">
                    <Breadcrumbs items={breadcrumbs} />
                </div>

                <div className="overflow-hidden rounded-xl bg-white shadow-lg">
                    <div className="grid md:grid-cols-2">

                        {/* Gallery Section */}
                        <div className="bg-gray-100 p-8">
                            <ImageGallery images={product.images} title={product.title} />

                            {/* Mockup Editor (Dynamic load) */}
                            <div className="mt-8">
                                <MockupLoader product={product} />
                            </div>
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

                            {product.color && product.color.trim() !== "" && (
                                <div className="mb-6 text-lg text-gray-600">
                                    <span className="font-bold">צבעים:</span> {product.color}
                                </div>
                            )}

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
                            {/* Actions */}
                            <div className="flex flex-col gap-4 border-t pt-8">

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

            <OrderSummary />
        </div >
    );
}

import MockupLoader from '@/components/MockupLoader';
