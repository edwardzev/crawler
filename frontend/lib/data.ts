import path from "path";
import fs from "fs/promises";
import { Product, CategoryNode, CategoryFlat } from "./types";

// Helper to determine data path
// In development, we read from ../data/out
// In production/build, we might need a different strategy if we deploy to Vercel.
// For Vercel, we can rely on `import` of JSON if it's small enough, or ensure data is copied to public.
// But user constraint says "Treat JSON snapshot as canonical build-time content".
// So we will assume they are available at build time.

const DATA_DIR = path.resolve(process.cwd(), "../data/out");
const PUBLIC_DATA_DIR = path.resolve(process.cwd(), "public/data");

// Fallback for Vercel deployment where sibling dirs might not be accessible easily
// unless we include them in the build.
// For this task, we assume local file system access during build.

export async function getProducts(): Promise<Product[]> {
    try {
        const primaryPath = path.join(DATA_DIR, "products.frontend.json");
        const fallbackPath = path.join(PUBLIC_DATA_DIR, "products.frontend.json");
        const filePath = await fileExists(primaryPath) ? primaryPath : fallbackPath;
        const data = await fs.readFile(filePath, "utf-8");
        return JSON.parse(data) as Product[];
    } catch (error) {
        console.error("Error loading products:", error);
        return [];
    }
}

export async function getCategoriesTree(): Promise<CategoryNode> {
    try {
        const primaryPath = path.join(DATA_DIR, "categories.frontend.json");
        const fallbackPath = path.join(PUBLIC_DATA_DIR, "categories.frontend.json");

        let filePath = "";
        if (await fileExists(primaryPath)) filePath = primaryPath;
        else if (await fileExists(fallbackPath)) filePath = fallbackPath;

        if (filePath) {
            const data = await fs.readFile(filePath, "utf-8");
            return JSON.parse(data) as CategoryNode;
        }

        // Fallback: Build from products if no pre-built tree exists
        console.warn("No pre-built categories.frontend.json found. Building from products...");
        const products = await getProducts();
        if (products.length > 0) {
            return buildCategoryTreeFromProducts(products);
        }

        return { name: "root", slug: "", count: 0, children: [] };
    } catch (error) {
        console.error("Error loading categories tree:", error);
        return { name: "root", slug: "", count: 0, children: [] };
    }
}

export async function getFlatCategories(): Promise<CategoryFlat[]> {
    try {
        const primaryPath = path.join(DATA_DIR, "categories.flat.json");
        const fallbackPath = path.join(PUBLIC_DATA_DIR, "categories.flat.json");
        const filePath = await fileExists(primaryPath) ? primaryPath : fallbackPath;
        const data = await fs.readFile(filePath, "utf-8");
        return JSON.parse(data) as CategoryFlat[];
    } catch (error) {
        console.error("Error loading flat categories:", error);
        return [];
    }
}

async function fileExists(filePath: string) {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
}

export function buildCategoryTreeFromProducts(products: Product[]): CategoryNode {
    const root: CategoryNode = {
        name: "root",
        slug: "",
        count: 0,
        children: []
    };

    const categoriesMap = new Map<string, CategoryNode>();

    for (const product of products) {
        root.count++;

        // Skip products with no category
        if (!product.category_path || product.category_path.length === 0) continue;

        let currentLevel = root;
        // Create/Update category nodes
        for (let i = 0; i < product.category_path.length; i++) {
            const catName = product.category_path[i];
            const catSlug = product.category_slug_path?.[i] || "";

            // Build a unique key path for the map
            const pathKey = product.category_slug_path.slice(0, i + 1).join("/");

            let node = categoriesMap.get(pathKey);

            if (!node) {
                node = {
                    name: catName,
                    slug: catSlug,
                    count: 0,
                    children: []
                };
                categoriesMap.set(pathKey, node);

                // Add to parent
                if (!currentLevel.children) currentLevel.children = [];
                currentLevel.children.push(node);
            }

            node.count++;
            currentLevel = node;
        }
    }

    return root;
}
