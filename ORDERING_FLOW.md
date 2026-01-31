# Multi-Product, Multi-Graphic Ordering Flow

## Overview

This document describes the enhanced ordering system that supports:
- Product variants (currently colors)
- Multiple graphics per product
- Multiple products per order

## Data Model

### Product Variants

Product variants are stored in the database `variant` field as JSON:

```json
{
  "type": "color",
  "options": [
    { "value": "black", "label": "Black" },
    { "value": "white", "label": "White" }
  ]
}
```

**Database Field**: `variant` (TEXT, JSON)

**Frontend Type**: `ProductVariant`

### Order Structure

An order consists of:
- **Order ID**: Airtable record ID
- **Items**: Array of graphics (1-5 per order)
- **Slots**: Graphics are assigned to slots 1-5

Each order item includes:
- Product information (title, SKU)
- Selected variant (if applicable)
- Graphic details (logo, mockup, width, quantity)
- Slot index (1-5)

## User Flow

### Step 1: Create Order Shell

When user adds first item:
1. System creates draft order via `/api/order/create`
2. Returns `order_id` stored in localStorage
3. Order remains in draft state

### Step 2: Add Product with Variant

For each product added:

1. **If product has variants**:
   - Display color selector in MockupEditor
   - User MUST select a color before adding to order
   - Selected variant is stored with the graphic

2. **Upload Logo**:
   - User uploads logo image
   - Can optionally remove background
   - Position and scale on canvas

3. **Configure Graphic**:
   - Set width in cm
   - Set quantity
   - Review mockup preview

4. **Add to Order**:
   - Validates variant selection (if required)
   - Gets next available slot (1-5)
   - Uploads logo + mockup to Cloudinary
   - Updates Airtable record
   - Adds to local order state

### Step 3: Persist to Backend

For each graphic added, the system:

1. **Uploads to Cloudinary**:
   - Folder: `orders/{order_id}/item_{slot_index}/`
   - Files: `logo.png`, `mockup.png`

2. **Updates Airtable**:
   - Sets `Graphic {N}` field (attachment)
   - Sets `Mockup {N}` field (attachment)
   - Sets `Width {N} cm` field (number)
   - Sets `Number {N}` field (number)
   - Appends to `Notes to Design` field

### Step 4: Add More Products

User can repeat Step 2 for:
- Same product with different variant
- Different product entirely

All graphics share the same order and slot pool.

### Step 5: Finalize Order

When user clicks "Send order":

1. Display finalization form:
   - Job Name
   - Deadline
   - Printing Method (DTF, UV, DTF-UV)
   - General Notes
   - Final approval checkbox

2. Submit via `/api/order/finalize`:
   - Updates order-level fields
   - Sets `Final check` = TRUE
   - Clears local order state

## Technical Details

### API Endpoints

#### `POST /api/order/create`
Creates draft order in Airtable.

**Response**:
```json
{ "order_id": "recXXXXXXXXXXXXXX" }
```

#### `POST /api/order/add-item`
Adds graphic to order.

**Form Parameters**:
- `order_id` (string)
- `slot_index` (1-5)
- `quantity` (number)
- `width` (float, cm)
- `logo` (file)
- `mockup` (file)
- `product_title` (string)
- `sku` (string)
- `variant_type` (string, optional) - e.g., "color"
- `variant_value` (string, optional) - e.g., "black"
- `variant_label` (string, optional) - e.g., "Black"

**Response**:
```json
{ "status": "success", "slot": 1 }
```

#### `POST /api/order/finalize`
Finalizes order with metadata.

**JSON Body**:
```json
{
  "order_id": "recXXXXXXXXXXXXXX",
  "job_name": "Company Event May 2024",
  "deadline": "2024-05-15",
  "method": "DTF",
  "notes": "Additional instructions...",
  "final_check": true
}
```

### Airtable Schema

**No schema changes required!** Uses existing fields:

**Per-Slot Fields** (1-5):
- `Graphic {N}` - Attachment (logo)
- `Mockup {N}` - Attachment (mockup preview)
- `Width {N} cm` - Number (width in cm)
- `Number {N}` - Number (quantity)

**Order-Level Fields**:
- `Job Name` - Single line text
- `Deadline` - Date
- `Method` - Single select (DTF, UV, DTF-UV)
- `Notes` - Long text
- `Notes to Design` - Long text (structured)
- `Final check` - Checkbox

### Notes to Design Format

Structured format for each graphic:

```
[PRODUCT]
SKU: TEST-001
Name: Test Product
Variant: Black (black)

[GRAPHIC]
Slot: 1
Width: 5.0 cm
Quantity: 100

========================================
[PRODUCT]
SKU: TEST-002
Name: Another Product
Variant: N/A

[GRAPHIC]
Slot: 2
Width: 7.5 cm
Quantity: 50
```

### Frontend State

**OrderState** (localStorage):
```typescript
{
  order_id: string | null,
  items: OrderItem[],
  used_slots: number[]  // [1, 2, 3]
}
```

**OrderItem**:
```typescript
{
  id: string,              // UUID
  product_title: string,
  sku: string,
  slot_index: number,      // 1-5
  width: number,
  quantity: number,
  logo_src: string,        // Base64 data URL
  mockup_src: string,      // Base64 data URL
  variant?: {              // Optional
    type: "color",
    value: "black",
    label: "Black"
  }
}
```

## Validation Rules

1. **Logo Upload**: Required before adding to order
2. **Variant Selection**: Required if product has variants
3. **Slot Availability**: Maximum 5 graphics per order
4. **Final Approval**: Must check "Final check" box before submission

## Backward Compatibility

✅ **Products without variants**: Work exactly as before
✅ **Existing orders**: Not affected
✅ **Airtable schema**: No changes required
✅ **API endpoints**: All parameters optional (variant_*)

## Example: Complete Order Flow

1. User browses catalog
2. Finds "Black T-Shirt" with color variants
3. Opens MockupEditor
4. Selects "Black" variant
5. Uploads logo
6. Configures: 100 qty, 5cm width
7. Clicks "Add to Order" → **Slot 1 used**
8. Continues shopping
9. Finds "White T-Shirt" (same product, different color)
10. Selects "White" variant
11. Uploads different logo
12. Configures: 50 qty, 7cm width
13. Clicks "Add to Order" → **Slot 2 used**
14. Reviews order summary (shows 2 items)
15. Clicks "Send Order"
16. Fills finalization form
17. Checks approval box
18. Submits → **Order complete!**

## Testing

### Test Product Data

See `/tmp/test_variant_product.json` for example product with variants.

### Manual Testing Checklist

- [ ] Product without variants displays normally
- [ ] Product with variants shows color selector
- [ ] Cannot add to order without selecting variant
- [ ] Can add same product with different variants
- [ ] Can add different products to same order
- [ ] Slot numbers increment correctly (1-5)
- [ ] Order summary shows all products with variants
- [ ] Cannot exceed 5 graphics per order
- [ ] Finalization form validates all required fields
- [ ] Successful order clears local state

## Future Enhancements

- Size variants
- Multiple variant types per product
- Variant-specific images
- Inventory validation
- Pricing calculation
- AI-powered logo placement
