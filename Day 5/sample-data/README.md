# Day 5 Sample Data

This directory contains all test data files for Day 5 demos. All demos reference these files to avoid duplication.

---

## Files Overview

| File | Purpose | Expected Result | Use In |
|------|---------|-----------------|--------|
| orders.csv | Valid 2-line order | ✅ Pass | All demos |
| orders-single-line.csv | Valid 1-line order | ✅ Pass | Demo 3, 4 |
| orders-multi-line.csv | Valid 5-line order | ✅ Pass | Demo 3, 4 |
| orders-invalid.csv | Invalid data (empty OrderNumber, bad date) | ❌ Fail | Demo 4 |
| orders-missing-required.csv | Missing required IDs | ❌ Fail | Demo 4 |
| x12-850-expected-output.txt | Sample X12 850 output | Reference | All demos |

---

## Valid Test Files

### 1. `orders.csv` ✅
**Standard test file - 2 line items**

```csv
OrderNumber,OrderDate,BuyerId,BuyerName,SellerId,SellerName,ShipToName,ShipToId,ShipToStreet,ShipToCity,ShipToState,ShipToPostal,LineNumber,ItemSku,ItemDescription,Quantity,UOM,UnitPrice
PO-1001,20240518,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,1,ABC-100,Widget A,10,EA,12.50
PO-1001,20240518,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,2,XYZ-200,Widget B,5,EA,25.00
```

**Details:**
- Order Number: PO-1001
- Order Date: May 18, 2024
- Buyer: Contoso Retail (BUYER01)
- Seller: Fabrikam Supplies (SELLER01)
- Ship To: Contoso DC (ST01) in Seattle, WA
- Line Items: 2
  - Line 1: 10 EA of Widget A @ $12.50
  - Line 2: 5 EA of Widget B @ $25.00

**Expected Output:**
- HTTP 200 OK
- Valid X12 850 message
- 2 PO1 segments with 2 PID segments

---

### 2. `orders-single-line.csv` ✅
**Minimal test file - 1 line item**

```csv
OrderNumber,OrderDate,BuyerId,BuyerName,SellerId,SellerName,ShipToName,ShipToId,ShipToStreet,ShipToCity,ShipToState,ShipToPostal,LineNumber,ItemSku,ItemDescription,Quantity,UOM,UnitPrice
PO-2001,20240520,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,1,ABC-100,Premium Widget,25,EA,15.99
```

**Details:**
- Order Number: PO-2001
- Order Date: May 20, 2024
- Line Items: 1
  - Line 1: 25 EA of Premium Widget @ $15.99

**Expected Output:**
- HTTP 200 OK
- Valid X12 850 message
- 1 PO1 segment with 1 PID segment

**Use for:**
- Testing minimal valid input
- Baseline validation
- Performance testing

---

### 3. `orders-multi-line.csv` ✅
**Complex test file - 5 line items**

```csv
OrderNumber,OrderDate,BuyerId,BuyerName,SellerId,SellerName,ShipToName,ShipToId,ShipToStreet,ShipToCity,ShipToState,ShipToPostal,LineNumber,ItemSku,ItemDescription,Quantity,UOM,UnitPrice
PO-3001,20240521,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,1,ABC-100,Widget A,10,EA,12.50
PO-3001,20240521,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,2,XYZ-200,Widget B,5,EA,25.00
PO-3001,20240521,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,3,DEF-300,Widget C,20,EA,8.75
PO-3001,20240521,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,4,GHI-400,Widget D,15,CS,45.00
PO-3001,20240521,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,5,JKL-500,Widget E,30,EA,6.25
```

**Details:**
- Order Number: PO-3001
- Order Date: May 21, 2024
- Line Items: 5 (various quantities and prices)

**Expected Output:**
- HTTP 200 OK
- Valid X12 850 message
- 5 PO1 segments with 5 PID segments

**Use for:**
- Testing multi-line order handling
- Performance testing with larger payloads
- Segment counting validation

---

## Invalid Test Files (Demo 4 Only)

### 4. `orders-invalid.csv` ❌
**Invalid data test file**

```csv
OrderNumber,OrderDate,BuyerId,BuyerName,SellerId,SellerName,ShipToName,ShipToId,ShipToStreet,ShipToCity,ShipToState,ShipToPostal,LineNumber,ItemSku,ItemDescription,Quantity,UOM,UnitPrice
,20240518,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,1,ABC-100,Widget A,10,EA,12.50
PO-1002,INVALID_DATE,BUYER01,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,2,XYZ-200,Widget B,5,EA,25.00
```

**Issues:**
- Line 1: Missing OrderNumber (empty BEG03)
- Line 2: Invalid date format "INVALID_DATE" (should be YYYYMMDD)

**Expected Output:**
- HTTP 400 Bad Request
- Validation errors:
  - "Element 'BEG03' is required but was empty"
  - "Invalid date format in BEG05"

**Use for:**
- Testing validation error handling
- Demonstrating error response format
- Training on data quality requirements

---

### 5. `orders-missing-required.csv` ❌
**Missing required fields test file**

```csv
OrderNumber,OrderDate,BuyerId,BuyerName,SellerId,SellerName,ShipToName,ShipToId,ShipToStreet,ShipToCity,ShipToState,ShipToPostal,LineNumber,ItemSku,ItemDescription,Quantity,UOM,UnitPrice
PO-1003,20240519,,Contoso Retail,SELLER01,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,1,ABC-100,Widget A,10,EA,12.50
PO-1003,20240519,BUYER01,Contoso Retail,,Fabrikam Supplies,Contoso DC,ST01,123 Warehouse Way,Seattle,WA,98101,2,XYZ-200,Widget B,5,EA,25.00
```

**Issues:**
- Line 1: Missing BuyerId (empty N104 for BY entity)
- Line 2: Missing SellerId (empty N104 for SE entity)

**Expected Output:**
- HTTP 400 Bad Request
- Validation errors:
  - "Element 'N104' is required when N103 is present"

**Use for:**
- Testing field-level validation
- Demonstrating impact of missing identifiers
- Understanding X12 data requirements

---

## Reference File

### 6. `x12-850-expected-output.txt` 📄
**Sample X12 850 EDI output**

Contains a complete X12 850 purchase order message showing expected format:

```
ISA*00*          *00*          *ZZ*BUYER01        *ZZ*SELLER01       *240518*1200*U*00401*000000001*0*T*>~
GS*PO*BUYER01*SELLER01*20240518*1200*1*X*004010~
ST*850*0001~
BEG*00*NE*PO-1001**20240518~
N1*BY*Contoso Retail*ZZ*BUYER01~
N1*SE*Fabrikam Supplies*ZZ*SELLER01~
N1*ST*Contoso DC*ZZ*ST01~
N3*123 Warehouse Way~
N4*Seattle*WA*98101~
PO1*1*10*EA*12.50**VP*ABC-100~
PID*F****Widget A~
PO1*2*5*EA*25.00**VP*XYZ-200~
PID*F****Widget B~
SE*13*0001~
GE*1*1~
IEA*1*000000001~
```

**Use for:**
- Reference for expected output format
- Understanding X12 850 structure
- Comparison during testing

---

## Testing Commands

### Demo 2 & 3 (No Validation)

```bash
# Test with standard file
curl -X POST "YOUR_LOGIC_APP_URL" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@Day 5/sample-data/orders.csv"

# Test with single line
curl -X POST "YOUR_LOGIC_APP_URL" \
  -F "file=@Day 5/sample-data/orders-single-line.csv"

# Test with multi-line
curl -X POST "YOUR_LOGIC_APP_URL" \
  -F "file=@Day 5/sample-data/orders-multi-line.csv"
```

**Expected:** HTTP 200 with X12 850 message

---

### Demo 4 (With Validation)

**Valid Files (Should Pass):**
```bash
# Standard test
curl -X POST "YOUR_LOGIC_APP_URL" \
  -F "file=@Day 5/sample-data/orders.csv"

# Single line test
curl -X POST "YOUR_LOGIC_APP_URL" \
  -F "file=@Day 5/sample-data/orders-single-line.csv"

# Multi-line test
curl -X POST "YOUR_LOGIC_APP_URL" \
  -F "file=@Day 5/sample-data/orders-multi-line.csv"
```

**Expected:** HTTP 200 with X12 850 message

**Invalid Files (Should Fail):**
```bash
# Test with invalid data
curl -X POST "YOUR_LOGIC_APP_URL" \
  -F "file=@Day 5/sample-data/orders-invalid.csv"

# Test with missing required fields
curl -X POST "YOUR_LOGIC_APP_URL" \
  -F "file=@Day 5/sample-data/orders-missing-required.csv"
```

**Expected:** HTTP 400 with validation error details

---

## PowerShell Commands

```powershell
# Valid test
Invoke-RestMethod -Method POST `
  -Uri "YOUR_LOGIC_APP_URL" `
  -ContentType "multipart/form-data" `
  -InFile "Day 5/sample-data/orders.csv"

# Invalid test
Invoke-RestMethod -Method POST `
  -Uri "YOUR_LOGIC_APP_URL" `
  -ContentType "multipart/form-data" `
  -InFile "Day 5/sample-data/orders-invalid.csv"
```

---

## CSV Field Reference

### Required Fields (Must Not Be Empty)
| Field | Maps To | Required For |
|-------|---------|--------------|
| OrderNumber | BEG03 | All validations |
| OrderDate | BEG05 | All validations (format: YYYYMMDD) |
| BuyerId | N1/N104 (BY) | N1 segment completeness |
| BuyerName | N1/N102 (BY) | Party identification |
| SellerId | N1/N104 (SE) | N1 segment completeness |
| SellerName | N1/N102 (SE) | Party identification |
| ShipToName | N1/N102 (ST) | Party identification |
| ShipToId | N1/N104 (ST) | N1 segment completeness |
| LineNumber | PO1/PO101 | Line item identification |
| Quantity | PO1/PO102 | Line item data |
| UOM | PO1/PO103 | Line item data |
| UnitPrice | PO1/PO104 | Line item data |

### Optional Fields (Can Be Empty)
| Field | Maps To | Notes |
|-------|---------|-------|
| ItemSku | PO1/PO107 | Product identifier |
| ItemDescription | PID/PID05 | Free-form description |
| ShipToStreet | N3/N301 | Address detail |
| ShipToCity | N4/N401 | Geographic location |
| ShipToState | N4/N402 | Geographic location |
| ShipToPostal | N4/N403 | Geographic location |

---

## Data Format Requirements

### Date Format
- **Required Format:** YYYYMMDD
- **Valid Examples:** 20240518, 20251225, 20230101
- **Invalid Examples:** 05/18/2024, 2024-05-18, 18-May-2024

### Identifiers
- **BuyerId/SellerId:** Alphanumeric, typically 5-10 characters
- **Examples:** BUYER01, SELLER01, CUST12345
- **ShipToId:** Alphanumeric, site/location code
- **Examples:** ST01, DC001, WAREHOUSE-A

### Quantities & Prices
- **Format:** Numeric strings
- **Decimals:** Allowed (e.g., "12.50", "99.99")
- **Integers:** Allowed (e.g., "10", "25")
- **Examples:** "10", "5.5", "1250.00"

### Unit of Measure (UOM)
- **Standard Codes:** EA (Each), CS (Case), BX (Box), LB (Pound)
- **Format:** 2-3 character codes
- **Examples:** EA, CS, BX, LB, KG, DZ

---

## Creating Custom Test Files

### Template
```csv
OrderNumber,OrderDate,BuyerId,BuyerName,SellerId,SellerName,ShipToName,ShipToId,ShipToStreet,ShipToCity,ShipToState,ShipToPostal,LineNumber,ItemSku,ItemDescription,Quantity,UOM,UnitPrice
PO-XXXX,YYYYMMDD,BUYERXX,Buyer Name Here,SELLERXX,Seller Name Here,Ship To Name,STXX,Street Address,City,ST,ZIP,1,SKU-001,Product Description,10,EA,99.99
```

### Multi-Line Orders
Same OrderNumber for all lines:
```csv
PO-1001,20240518,...,1,SKU-001,Item 1,...
PO-1001,20240518,...,2,SKU-002,Item 2,...
PO-1001,20240518,...,3,SKU-003,Item 3,...
```

---

## Troubleshooting

### Issue: Validation fails with null errors

**Check:**
1. Schema name in Logic App matches uploaded schema
   - Logic App: `X12_850_PurchaseOrder`
   - Integration Account: Must match exactly
2. XSLT uses correct element names
   - Should be: `<N1Loop>`, `<PO1Loop>`
   - NOT: `<N1Loop1>`, `<PO1Loop1>`
3. All schemas uploaded to Integration Account
   - `orders-flatfile` (CSV schema)
   - `CsvToX12_850` (XSLT map)
   - `X12_850_PurchaseOrder` (X12 validation schema)

### Issue: All files fail validation

**Check:**
1. Correct XSLT uploaded from `Day 5/schemas/CsvToX12_850.xslt`
2. Namespace matches in XSLT and XSD
3. Integration Account linked to Logic App

### Issue: Date format errors

**Fix:** Use YYYYMMDD format (e.g., 20240518, not 05/18/2024)

---

## Related Documentation

- **Schemas:** [Day 5/schemas/README.md](../schemas/README.md)
- **XSLT Map:** [Day 5/schemas/CsvToX12_850.xslt](../schemas/CsvToX12_850.xslt)
- **Compatibility:** [Day 5/schemas/COMPATIBILITY_TEST.md](../schemas/COMPATIBILITY_TEST.md)
- **Demo 4 Guide:** [Day 5/Demo 4/README.md](../Demo%204/README.md)

---

**Last Updated:** 2025-12-23
**Sample Data Version:** 1.0
