import { getProducts, getFlatCategories } from "@/lib/data";
import { MetadataRoute } from "next";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    const baseUrl = "https://example.com"; // Should be env var

    const products = await getProducts();
    const flatCategories = await getFlatCategories();

    const productUrls = products.map((p) => ({
        url: `${baseUrl}/p/${p.id}/${p.slug}`,
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
