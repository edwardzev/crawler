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
        const filePath = await fileExists(primaryPath) ? primaryPath : fallbackPath;
        const data = await fs.readFile(filePath, "utf-8");
        return JSON.parse(data) as CategoryNode;
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
