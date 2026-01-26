# Mockup Editor Feature

A client-side logo placement tool integrated into the product page.
Allows users to upload a logo, position it on the product image, and share via WhatsApp.

## How to Run Locally

1. Ensure dependencies are installed:
   ```bash
   cd frontend
   npm install
   ```
   (Requires `fabric` and `uuid`)

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Navigate to any product page, e.g.:
   `http://localhost:3000/p/kraus/CR30/cr30...`

4. Scroll down to the "Mockup Editor" section (below the main gallery).

## Storage

- Mockups are saved as JSON files in:
  `frontend/public/data/mockups/<id>.json`
- This directory is git-ignored (except `.gitkeep`).
- In production, this folder must be writable or replaced with a database/S3 storage driver in `app/api/mockups/route.ts`.

## Environment Variables

- `NEXT_PUBLIC_BASE_URL`: Used for generating share links. Defaults to `window.location.origin` in client, ensuring correct links.
- WhatsApp number is currently hardcoded in `MockupEditor.tsx` (Change `972501234567` if needed).

## Testing

1. **Upload**: Click "Upload Logo" and select a PNG/JPG.
2. **Transform**: Drag, Resize, Rotate the logo on canvas.
3. **Share**: Click "Send on WhatsApp".
   - Should open WhatsApp Web.
   - Message should contain a link like `http://.../m/<uuid>`.
4. **View**: Open the link.
   - Should see the same logo placement (read-only mode).
   - "Original Product" link should work.
