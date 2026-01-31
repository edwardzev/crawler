# System Architecture - Multi-Product Variant Ordering

## Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Product Page (Next.js)                                   │  │
│  │  - ImageGallery                                           │  │
│  │  - MockupLoader → MockupEditor                           │  │
│  │    ├─ Variant Selector (if product.variant exists)      │  │
│  │    ├─ Logo Upload (Fabric.js canvas)                    │  │
│  │    ├─ Quantity & Width inputs                           │  │
│  │    └─ Add to Order button                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  useOrder Hook (State Management)                         │  │
│  │  - LocalStorage: order_id, items[], used_slots[]        │  │
│  │  - getNextSlot() → Returns 1-5 or null                  │  │
│  │  - addItem(itemData, logoBlob, mockupBlob)              │  │
│  │  - finalizeOrder(finalData)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  OrderSummary (Floating Component)                        │  │
│  │  - Shows all items with variants                         │  │
│  │  - Finalization form                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────┬───────────────────────────────────────┘
                         │ API Calls (Fetch)
                         ↓
┌────────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER (FastAPI)                     │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  POST /api/order/create                                        │
│  └─→ Creates draft order in Airtable                          │
│      Returns: { order_id }                                     │
│                                                                 │
│  POST /api/order/add-item (FormData)                          │
│  ├─→ Uploads logo + mockup to Cloudinary                     │
│  │   Folder: orders/{order_id}/item_{slot}/                  │
│  ├─→ Updates Airtable record                                 │
│  │   Fields: Graphic N, Mockup N, Width N cm, Number N      │
│  └─→ Appends structured notes to "Notes to Design"           │
│      [PRODUCT] SKU: ... Variant: ...                          │
│      [GRAPHIC] Slot: ... Width: ... Quantity: ...             │
│                                                                 │
│  POST /api/order/finalize (JSON)                              │
│  └─→ Updates order-level fields                              │
│      Job Name, Deadline, Method, Notes, Final check           │
│                                                                 │
└────────────┬──────────────────────┬────────────────────────────┘
             │                      │
             ↓                      ↓
┌─────────────────────┐   ┌──────────────────────┐
│    Cloudinary       │   │     Airtable         │
│                     │   │                      │
│  orders/            │   │  Orders Table        │
│  └─ {order_id}/     │   │  ├─ Graphic 1-5      │
│     ├─ item_1/      │   │  ├─ Mockup 1-5       │
│     │  ├─ logo.png  │   │  ├─ Width 1-5 cm     │
│     │  └─ mockup.png│   │  ├─ Number 1-5       │
│     ├─ item_2/      │   │  ├─ Job Name         │
│     │  └─ ...       │   │  ├─ Deadline         │
│     └─ ...          │   │  ├─ Method           │
│                     │   │  ├─ Notes            │
│                     │   │  ├─ Notes to Design  │
│                     │   │  └─ Final check      │
└─────────────────────┘   └──────────────────────┘


## Data Flow

1. Product Data Loading
   ┌─────────────┐
   │ Database    │
   │ products.db │
   │ - variant   │ (JSON: {"type":"color","options":[...]})
   └──────┬──────┘
          │ FrontendExporter.export()
          ↓
   ┌─────────────────────────┐
   │ data/out/               │
   │ products.frontend.json  │
   │ - variant: {...}        │
   └──────┬──────────────────┘
          │ Copy to frontend/public/data/
          ↓
   ┌─────────────────────┐
   │ Next.js Static Gen  │
   │ getProducts()       │
   └──────┬──────────────┘
          │
          ↓
   ┌─────────────────────┐
   │ Product Page        │
   │ - product.variant   │
   └─────────────────────┘

2. Order Creation Flow
   User clicks "Add to Order"
          ↓
   Validate variant selected (if required)
          ↓
   Generate logo + mockup blobs
          ↓
   Get next available slot (1-5)
          ↓
   POST /api/order/add-item
          ↓
   ┌──────────────────────┐
   │ Upload to Cloudinary │
   └──────────────────────┘
          │
          ↓
   ┌──────────────────────┐
   │ Update Airtable      │
   │ - Set slot fields    │
   │ - Append notes       │
   └──────────────────────┘
          │
          ↓
   Update local state (localStorage)
          ↓
   Show in OrderSummary

3. Order Finalization
   User clicks "Send Order"
          ↓
   Show FinalizeOrderForm
          ↓
   User fills:
   - Job Name
   - Deadline
   - Method (DTF/UV/DTF-UV)
   - Notes
   - Final check ✓
          ↓
   POST /api/order/finalize
          ↓
   Update Airtable order-level fields
          ↓
   Clear localStorage
          ↓
   Order complete!


## Type Definitions

Product (TypeScript)
{
  catalog_id: string
  sku_clean: string
  supplier_slug: string
  title: string
  sku: string
  images: string[]
  variant?: {                    // NEW
    type: "color"
    options: [
      { value: "black", label: "שחור" },
      { value: "white", label: "לבן" }
    ]
  }
  ...
}

OrderItem (TypeScript)
{
  id: string                     // UUID
  product_title: string
  sku: string
  slot_index: number             // 1-5
  width: number
  quantity: number
  logo_src: string               // Base64
  mockup_src: string             // Base64
  variant?: {                    // NEW
    type: "color"
    value: "black"
    label: "שחור"
  }
}

OrderState (LocalStorage)
{
  order_id: string | null        // Airtable record ID
  items: OrderItem[]
  used_slots: number[]           // [1, 2, 3]
}


## Validation Rules

1. Logo Upload
   - Required before adding to order
   - Format: Any image type
   - Processing: Fabric.js canvas

2. Variant Selection
   - Required if product.variant exists
   - Validated before API call
   - Shows error message if missing

3. Slot Availability
   - Maximum 5 graphics per order
   - getNextSlot() returns null if full
   - Error shown to user

4. Order Finalization
   - Job Name: Required
   - Deadline: Required
   - Method: Required (dropdown)
   - Final check: Must be checked
   - All validated before submission


## Backward Compatibility

Products WITHOUT variants:
{
  catalog_id: "supplier:sku"
  variant: null               // or undefined
  ...
}
→ No color selector shown
→ Ordering flow unchanged
→ API receives null variant
→ Airtable shows "Variant: N/A"

Products WITH variants:
{
  catalog_id: "supplier:sku"
  variant: {
    type: "color"
    options: [...]
  }
  ...
}
→ Color selector shown
→ Validation enforced
→ API receives variant data
→ Airtable shows "Variant: Black (black)"


## Deployment Checklist

Backend:
[ ] Set AIRTABLE_PAT environment variable
[ ] Set CLOUDINARY_URL environment variable
[ ] Run database migration (automatic on first start)
[ ] Start server: uvicorn server:app --reload

Frontend:
[ ] Install dependencies: npm install
[ ] Copy data: cp data/out/*.json frontend/public/data/
[ ] Build: npm run build (or npm run dev)
[ ] Verify TypeScript: npx tsc --noEmit

Data:
[ ] Add products with variants to database
[ ] Export to frontend: FrontendExporter.export()
[ ] Verify JSON structure

Testing:
[ ] Test product without variants (backward compat)
[ ] Test product with variants (new flow)
[ ] Test multiple products in one order
[ ] Test slot allocation (1-5)
[ ] Test order finalization
[ ] Verify Airtable records
[ ] Verify Cloudinary uploads


## Performance Notes

- LocalStorage: ~10KB per order (5 items with base64 thumbnails)
- Cloudinary: ~2MB per order (5 full-res mockups)
- Airtable: 1 record per order
- Database: Variant field adds ~500 bytes per product with variants

## Security Considerations

- Variant data is user-controlled (validate on frontend)
- File uploads are validated by Cloudinary
- Airtable API key stored server-side only
- No sensitive data in LocalStorage
- CORS configured for API endpoints
