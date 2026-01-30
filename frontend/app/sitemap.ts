import { getProducts, getFlatCategories } from "@/lib/data";
import { MetadataRoute } from "next";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    const baseUrl = (process.env.NEXT_PUBLIC_BASE_URL || "https://example.com").replace(/\/$/, "");

    const products = await getProducts();
    const flatCategories = await getFlatCategories();

    const productUrls = products
        .filter(p => p.supplier_slug && p.sku_clean)
        .map((p) => ({
            url: `${baseUrl}/p/${p.supplier_slug}/${p.sku_clean}/${p.slug}`,
            lastModified: p.last_seen_at ? new Date(p.last_seen_at) : new Date(),
        }));

    const categoryUrls = flatCategories.map((c) => ({
        url: `${baseUrl}/c/${c.slug_path.join("/")}`,
        lastModified: new Date(),
    }));

    return [
        {
            url: baseUrl,
            lastModified: new Date(),
        },
        ...categoryUrls,
        ...productUrls,
    ];
}
