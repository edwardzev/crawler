import { NextRequest, NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { v4 as uuidv4 } from "uuid";

// We store mockups in data/out/mockups/
const MOCKUP_STORAGE_DIR = path.resolve(process.cwd(), "public/data/mockups");
// Note: storing in 'public' makes it essentially a static file server for GET requests if we wanted simple hosting,
// but usually we want to control reads. Since requirement asks to store under /data/mockups/ and dev mode:
// We'll put it in public/data/mockups so it persists and is servable if needed, OR process.cwd()/../data if we want strict backend.
// Requirement said: "/data/mockups/" (relative to repo root potentially).
// Let's stick to `public/data/mockups` for easiest dev persistence in Next.js without external DB.

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();

        // Basic validation
        if (!body.catalog_id || !body.transform) {
            return NextResponse.json({ error: "Invalid payload" }, { status: 400 });
        }

        // Generate ID (short 8 char for cleaner URLs, or uuid)
        const id = uuidv4().slice(0, 8);
        const filename = `${id}.json`;

        // Ensure dir exists
        await fs.mkdir(MOCKUP_STORAGE_DIR, { recursive: true });

        // Save file
        // Sanitize? We store exactly what they send for now, it's dev mode.
        // We add server timestamp.
        const record = {
            id,
            createdAt: new Date().toISOString(),
            ...body
        };

        await fs.writeFile(path.join(MOCKUP_STORAGE_DIR, filename), JSON.stringify(record, null, 2));

        return NextResponse.json({ id, success: true });

    } catch (error) {
        console.error("Mockup save error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}
