import { NextResponse } from 'next/server';
import { getProducts } from '@/lib/data';
import { searchProducts } from '@/lib/search';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q');

    if (!query) {
        return NextResponse.json([]);
    }

    const products = await getProducts();
    // Return top 5 results
    const results = searchProducts(products, query).slice(0, 5);

    return NextResponse.json(results);
}
