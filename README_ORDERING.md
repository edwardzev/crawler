# Custom Ordering System - Implementation Guide

## Quick Start

### 1. Add Product with Variants

Use the provided script to add a test product:

```bash
python3 scripts/add_test_variant_product.py
```

This creates a product with color variants (Black, White, Navy).

### 2. Export to Frontend

```bash
python3 -c "from crawler.exporter import FrontendExporter; FrontendExporter('products.db', 'data/out').export()"
```

### 3. Copy to Frontend

```bash
mkdir -p frontend/public/data
cp data/out/*.json frontend/public/data/
```

### 4. Start Backend Server

```bash
# Set environment variables
export AIRTABLE_PAT="your_airtable_pat"
export CLOUDINARY_URL="cloudinary://api_key:api_secret@cloud_name"

# Run server
uvicorn server:app --reload
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

## Product Variant Structure

To enable variant support for a product, add a `variant` field to the database:

```sql
UPDATE products 
SET variant = '{"type":"color","options":[{"value":"black","label":"Black"},{"value":"white","label":"White"}]}'
WHERE catalog_id = 'supplier:sku';
```

Or using Python:

```python
import sqlite3
import json

conn = sqlite3.connect('products.db')
c = conn.cursor()

variant_data = {
    "type": "color",
    "options": [
        {"value": "black", "label": "שחור"},
        {"value": "white", "label": "לבן"}
    ]
}

c.execute(
    "UPDATE products SET variant = ? WHERE catalog_id = ?",
    (json.dumps(variant_data), "supplier:sku")
)

conn.commit()
conn.close()
```

## Airtable Setup

### Required Fields

The system uses these Airtable fields (already existing):

**Per-Slot (1-5):**
- `Graphic 1` ... `Graphic 5` (Attachment)
- `Mockup 1` ... `Mockup 5` (Attachment)
- `Width 1 cm` ... `Width 5 cm` (Number)
- `Number 1` ... `Number 5` (Number)

**Order Level:**
- `Job Name` (Single line text)
- `Deadline` (Date)
- `Method` (Single select: DTF, UV, DTF-UV)
- `Notes` (Long text)
- `Notes to Design` (Long text)
- `Final check` (Checkbox)

### Environment Variables

```bash
# Airtable
AIRTABLE_PAT=patXXXXXXXXXXXXXX
# Base ID and Table Name are hardcoded in server.py

# Cloudinary
CLOUDINARY_URL=cloudinary://123456789012345:abcdefghijklmnopqrstuvwxyz@yourcloud
```

## User Flow Example

### Scenario: Ordering Two Different Products

1. **First Product: Black T-Shirt**
   - User navigates to product page
   - Sees color selector: Black, White, Navy
   - Selects "Black"
   - Uploads logo
   - Sets: 100 qty, 5cm width
   - Clicks "Add to Order"
   - **Result**: Slot 1 assigned

2. **Second Product: White T-Shirt**
   - Same product, different color
   - Selects "White"
   - Uploads different logo
   - Sets: 50 qty, 7cm width
   - Clicks "Add to Order"
   - **Result**: Slot 2 assigned

3. **Review Order**
   - Order summary shows 2 items
   - Item 1: Black T-Shirt (100 pcs, 5cm)
   - Item 2: White T-Shirt (50 pcs, 7cm)

4. **Finalize**
   - Clicks "Send Order"
   - Fills: Job Name, Deadline, Method
   - Checks approval box
   - Submits
   - **Result**: Order sent to Airtable

## API Reference

### POST /api/order/create

Creates a new draft order.

**Response:**
```json
{
  "order_id": "recXXXXXXXXXXXXXX"
}
```

### POST /api/order/add-item

Adds a graphic to the order.

**Form Data:**
- `order_id`: string (required)
- `slot_index`: number 1-5 (required)
- `quantity`: number (required)
- `width`: number (cm, required)
- `logo`: file (required)
- `mockup`: file (required)
- `product_title`: string (required)
- `sku`: string (required)
- `variant_type`: string (optional)
- `variant_value`: string (optional)
- `variant_label`: string (optional)

**Response:**
```json
{
  "status": "success",
  "slot": 1
}
```

### POST /api/order/finalize

Finalizes the order with metadata.

**JSON Body:**
```json
{
  "order_id": "recXXXXXXXXXXXXXX",
  "job_name": "Company Event",
  "deadline": "2024-05-15",
  "method": "DTF",
  "notes": "Rush order",
  "final_check": true
}
```

**Response:**
```json
{
  "status": "success"
}
```

## Frontend Components

### MockupEditor

Displays product mockup editor with variant selector.

**Props:**
```typescript
{
  product: Product,        // Product data with optional variant
  initialState?: any,      // For loading saved mockups
  readOnly?: boolean,      // View-only mode
  onClose?: () => void     // Close callback
}
```

**Features:**
- Color variant selector (if product has variants)
- Logo upload and positioning
- Background removal (AI)
- Opacity and blend mode controls
- Quantity and width inputs
- Validation before adding to order

### OrderSummary

Shows floating order summary with all items.

**Features:**
- Displays all graphics in order
- Shows variant selection per item
- Slot numbers
- Quantities and widths
- Finalization button

### useOrder Hook

Manages order state in localStorage.

**API:**
```typescript
{
  orderState: OrderState,
  addItem: (itemData, logoBlob, mockupBlob) => Promise<OrderItem>,
  finalizeOrder: (finalData) => Promise<boolean>,
  resetOrder: () => void,
  isLoaded: boolean,
  getNextSlot: () => number | null
}
```

## Database Schema

The `variant` field is a TEXT column containing JSON:

```sql
CREATE TABLE products (
  ...
  variant TEXT,  -- JSON: {"type":"color","options":[...]}
  ...
);
```

## Validation Rules

1. **Logo Required**: Cannot add to order without logo
2. **Variant Required**: If product has variants, selection is mandatory
3. **Slot Limit**: Maximum 5 graphics per order
4. **Final Approval**: Must check approval box before submission
5. **Order Fields**: Job name and deadline are required

## Troubleshooting

### Product doesn't show variant selector

1. Check if `variant` field exists in database
2. Verify variant JSON structure is correct
3. Re-export frontend data
4. Clear browser localStorage

### Airtable upload fails

1. Check AIRTABLE_PAT is set correctly
2. Verify base ID and table name
3. Check field names match exactly
4. Review Airtable API limits

### Cloudinary upload fails

1. Check CLOUDINARY_URL format
2. Verify credentials are correct
3. Check network connectivity
4. Review Cloudinary storage limits

## Development Tips

### Testing Variants Locally

1. Add test products with variants using the script
2. Export to frontend JSON
3. Start backend with test credentials
4. Use browser dev tools to inspect state
5. Check Airtable records in sandbox base

### Debugging Order Flow

1. Check browser console for errors
2. Review localStorage for order state
3. Check Network tab for API calls
4. Verify Cloudinary folder structure
5. Check Airtable "Notes to Design" field

## Future Enhancements

- [ ] Size variants
- [ ] Multiple variant types per product
- [ ] Variant-specific product images
- [ ] Inventory validation per variant
- [ ] Price calculation based on variants
- [ ] Bulk variant management UI
- [ ] AI-powered logo placement

## Support

For issues or questions:
1. Check ORDERING_FLOW.md for detailed flow
2. Review this README for setup instructions
3. Check the test script for examples
4. Review Airtable schema setup
