# Order Processing System - X12 850 Test Examples

This document provides curl commands to test the Order Processing System with X12 850 Purchase Order messages.

## Prerequisites

Set the following environment variables:

```bash
# Logic App HTTP endpoint (get from Azure Portal after deployment)
export LOGIC_APP_URL="https://your-logic-app-url.azurewebsites.net:443/workflows/xxx/triggers/HTTP_Request_-_Receive_X12_Order/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FHTTP_Request_-_Receive_X12_Order%2Frun&sv=1.0&sig=xxx"

# Azure Function URL (for direct function testing)
export FUNCTION_URL="http://localhost:7071/api/process-order"
# Or deployed: export FUNCTION_URL="https://your-function.azurewebsites.net/api/process-order"

# X12 Mapping Function URL (for mapping only)
export MAPPING_URL="http://localhost:7071/api/x12-map"
```

---

## 1. Test Full Order Processing (X12 850)

### 1.1 Complete X12 850 Purchase Order

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*PO-2024-001**20240115~CUR*BY*USD~REF*DP*DEPT-100~REF*IA*ACCT-5001~PER*BD*John Smith*TE*555-123-4567*EM*john.smith@buyer.com~N1*BY*Acme Corporation*92*ACME-001~N3*100 Main Street*Suite 500~N4*Seattle*WA*98101*US~N1*ST*Acme Warehouse*92*WH-001~N3*200 Distribution Way~N4*Portland*OR*97201*US~N1*SE*Tech Supplies Inc*92*TECH-001~PO1*001*10*EA*29.99*PE*VP*MOUSE-W100*BP*1234567890~PID*F****Wireless Mouse - Black~PO1*002*5*EA*49.99*PE*VP*KB-USB200*BP*2345678901~PID*F****USB Keyboard - Full Size~PO1*003*2*EA*199.99*PE*VP*MON-24HD*BP*3456789012~PID*F****24-inch HD Monitor~CTT*3*17~AMT*TT*849.83~SE*20*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850",
    "client": "acme"
  }'
```

**Expected Response (201 Created):**
```json
{
  "success": true,
  "message": "Order processed successfully",
  "orderId": "ORD-20240115-A1B2C3D4",
  "orderDate": "2024-01-15T10:30:00.000Z",
  "status": "pending",
  "summary": {
    "purchaseOrderNumber": "PO-2024-001",
    "buyer": "Acme Corporation",
    "itemCount": 3,
    "totalAmount": 849.83
  },
  "storage": {
    "database": "Order saved to PostgreSQL",
    "blobPath": "order-documents/2024/01/15/ORD-20240115-A1B2C3D4.json"
  },
  "warnings": []
}
```

### 1.2 Minimal X12 850 Order

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*NE*PO-MIN-001**20240115~N1*BY*Quick Buyer Inc*92*QB-001~PO1*001*25*EA*15.00**VP*WIDGET-001~CTT*1*25~SE*6*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }'
```

### 1.3 X12 850 with Multiple Line Items

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*BIGORDER       *ZZ*SUPPLIER       *240115*1400*U*00401*000000002*0*P*:~GS*PO*BIGORDER*SUPPLIER*20240115*1400*2*X*004010~ST*850*0002~BEG*00*SA*PO-BULK-2024-001**20240115~CUR*BY*USD~N1*BY*Enterprise Corp*92*ENT-001~N3*500 Corporate Blvd~N4*Chicago*IL*60601*US~N1*ST*Enterprise Warehouse*92*EW-001~N3*1000 Logistics Lane~N4*Indianapolis*IN*46201*US~PO1*001*100*EA*5.99*PE*VP*CABLE-HDMI-6FT~PID*F****HDMI Cable 6 Foot~PO1*002*200*EA*3.49*PE*VP*CABLE-USB-C-3FT~PID*F****USB-C Cable 3 Foot~PO1*003*50*EA*12.99*PE*VP*ADAPTER-USBC-HDMI~PID*F****USB-C to HDMI Adapter~PO1*004*75*EA*8.99*PE*VP*HUB-USB-4PORT~PID*F****4-Port USB Hub~PO1*005*30*EA*24.99*PE*VP*CHARGER-USBC-65W~PID*F****65W USB-C Charger~CTT*5*455~AMT*TT*3571.30~SE*18*0002~GE*1*2~IEA*1*000000002~",
    "transactionSet": "850"
  }'
```

---

## 2. Test X12 Mapping Only (No Storage)

### 2.1 Map X12 to JSON Without Processing

```bash
curl -X POST "$MAPPING_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*TEST-PO-001**20240115~N1*BY*Test Buyer*92*TB-001~PO1*001*5*EA*99.99*PE*VP*PROD-001~CTT*1*5~SE*6*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850",
    "includeMeta": true
  }'
```

**Expected Response:**
```json
{
  "mappingPath": "mapping/standards/850.json",
  "segmentCount": 12,
  "output": {
    "purchaseOrderNumber": "TEST-PO-001",
    "purchaseOrderDate": "2024-01-15",
    "purchaseOrderType": "Original",
    "purchaseOrderTypeCode": "Stand-alone Order",
    "buyer": {
      "name": "Test Buyer",
      "qualifierCode": "92",
      "id": "TB-001"
    },
    "items": [
      {
        "lineNumber": "001",
        "quantity": 5,
        "unitOfMeasure": "EA",
        "unitPrice": 99.99,
        "productIdQualifier": "VP",
        "productId": "PROD-001"
      }
    ],
    "summary": {
      "totalLineItems": "1",
      "hashTotal": "5"
    }
  }
}
```

---

## 3. Test via Logic App

### 3.1 Send X12 Order to Logic App

```bash
curl -X POST "$LOGIC_APP_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*LOGICTEST      *ZZ*RECEIVER       *240115*1500*U*00401*000000003*0*P*:~GS*PO*LOGICTEST*RECEIVER*20240115*1500*3*X*004010~ST*850*0003~BEG*00*SA*LA-PO-001**20240115~CUR*BY*USD~N1*BY*Logic App Test Corp*92*LATC-001~N3*789 Workflow Avenue~N4*Austin*TX*78701*US~PO1*001*3*EA*299.99*PE*VP*LAPTOP-BASIC~PID*F****Basic Laptop Computer~PO1*002*3*EA*49.99*PE*VP*LAPTOP-BAG~PID*F****Laptop Carrying Bag~CTT*2*6~AMT*TT*1049.94~SE*12*0003~GE*1*3~IEA*1*000000003~",
    "transactionSet": "850"
  }'
```

---

## 4. Test Error Cases

### 4.1 Invalid X12 - Missing Required Segments

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA***20240115~SE*3*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "success": false,
  "orderId": "ORD-20240115-XXXXXXXX",
  "message": "Order validation failed",
  "errors": [
    "purchaseOrderNumber is required (BEG03)",
    "At least one line item is required (PO1)"
  ],
  "warnings": [
    "purchaseOrderDate is recommended (BEG05)",
    "buyer.name is recommended (N1-BY)"
  ],
  "validatedAt": "2024-01-15T10:30:00.000Z"
}
```

### 4.2 Missing X12 Data

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "transactionSet": "850"
  }'
```

**Expected Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "x12 or segments is required."
}
```

### 4.3 Invalid JSON

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d 'not valid json'
```

**Expected Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Request body must be valid JSON."
}
```

---

## 5. Pre-Parsed Segments Format

### 5.1 Using Pre-Parsed Segments Instead of Raw X12

```bash
curl -X POST "$FUNCTION_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "segments": [
      {"id": "ISA", "elements": ["00", "          ", "00", "          ", "ZZ", "SENDER         ", "ZZ", "RECEIVER       ", "240115", "1030", "U", "00401", "000000001", "0", "P", ":"]},
      {"id": "GS", "elements": ["PO", "SENDER", "RECEIVER", "20240115", "1030", "1", "X", "004010"]},
      {"id": "ST", "elements": ["850", "0001"]},
      {"id": "BEG", "elements": ["00", "SA", "SEGMENT-PO-001", "", "20240115"]},
      {"id": "N1", "elements": ["BY", "Segment Test Buyer", "92", "STB-001"]},
      {"id": "PO1", "elements": ["001", "10", "EA", "25.00", "PE", "VP", "SEG-PROD-001"]},
      {"id": "PID", "elements": ["F", "", "", "", "Test Product from Segments"]},
      {"id": "CTT", "elements": ["1", "10"]},
      {"id": "SE", "elements": ["8", "0001"]},
      {"id": "GE", "elements": ["1", "1"]},
      {"id": "IEA", "elements": ["1", "000000001"]}
    ],
    "transactionSet": "850"
  }'
```

---

## 6. Sample X12 850 Messages

### 6.1 Standard Retail Order

```
ISA*00*          *00*          *ZZ*RETAILER       *ZZ*VENDOR         *240115*0900*U*00401*000000001*0*P*:~
GS*PO*RETAILER*VENDOR*20240115*0900*1*X*004010~
ST*850*0001~
BEG*00*SA*RETAIL-2024-0001**20240115~
CUR*BY*USD~
REF*DP*CLOTHING~
N1*BY*Fashion Retail Store*92*FRS-001~
N3*123 Shopping Center Dr~
N4*Los Angeles*CA*90001*US~
N1*ST*Fashion Distribution Center*92*FDC-001~
N3*456 Warehouse Blvd~
N4*Ontario*CA*91761*US~
PO1*001*50*EA*39.99*PE*VP*SHIRT-BLU-M~
PID*F****Blue Cotton Shirt - Medium~
PO1*002*50*EA*39.99*PE*VP*SHIRT-BLU-L~
PID*F****Blue Cotton Shirt - Large~
PO1*003*30*EA*59.99*PE*VP*JEANS-BLK-32~
PID*F****Black Denim Jeans - Size 32~
CTT*3*130~
AMT*TT*5799.20~
SE*16*0001~
GE*1*1~
IEA*1*000000001~
```

### 6.2 B2B Industrial Order

```
ISA*00*          *00*          *ZZ*MANUFACTURER   *ZZ*SUPPLIER       *240115*1100*U*00401*000000002*0*P*:~
GS*PO*MANUFACTURER*SUPPLIER*20240115*1100*2*X*004010~
ST*850*0002~
BEG*00*RC*MFG-PO-2024-0500*CONTRACT-2023-001*20240115~
CUR*BY*USD~
REF*CO*CONTRACT-2023-001~
DTM*002*20240201~
DTM*010*20240125~
N1*BY*Industrial Manufacturing Co*01*123456789~
N3*1000 Factory Road~
N4*Detroit*MI*48201*US~
PER*BD*Procurement Dept*TE*313-555-0100*EM*procurement@mfg.com~
N1*ST*IMC Assembly Plant*92*IMCAP-001~
N3*2000 Assembly Drive~
N4*Toledo*OH*43601*US~
N1*SE*Parts Supply Corp*01*987654321~
PO1*001*1000*EA*2.50*PE*VP*BOLT-HEX-M8~
PID*F****Hex Bolt M8 x 25mm Grade 8.8~
PO1*002*1000*EA*0.35*PE*VP*NUT-HEX-M8~
PID*F****Hex Nut M8 Grade 8~
PO1*003*2000*EA*0.15*PE*VP*WASHER-FLAT-M8~
PID*F****Flat Washer M8 Zinc~
PO1*004*500*EA*8.75*PE*VP*BEARING-6205~
PID*F****Ball Bearing 6205-2RS~
CTT*4*4500~
AMT*TT*7475.00~
SE*22*0002~
GE*1*2~
IEA*1*000000002~
```

---

## 7. PowerShell Examples

### 7.1 Send X12 Order via PowerShell

```powershell
$x12Message = @"
ISA*00*          *00*          *ZZ*POWERSHELL     *ZZ*RECEIVER       *240115*1200*U*00401*000000001*0*P*:~GS*PO*POWERSHELL*RECEIVER*20240115*1200*1*X*004010~ST*850*0001~BEG*00*SA*PS-ORDER-001**20240115~N1*BY*PowerShell Test Corp*92*PSTC-001~PO1*001*5*EA*149.99*PE*VP*PWSH-PROD-001~CTT*1*5~SE*6*0001~GE*1*1~IEA*1*000000001~
"@

$body = @{
    x12 = $x12Message
    transactionSet = "850"
} | ConvertTo-Json

Invoke-RestMethod -Uri $env:FUNCTION_URL -Method Post -Body $body -ContentType "application/json"
```

---

## 8. X12 850 Segment Reference

| Segment | Description | Key Elements |
|---------|-------------|--------------|
| ISA | Interchange Control Header | Sender/Receiver IDs, Date, Time |
| GS | Functional Group Header | Transaction Type, Version |
| ST | Transaction Set Header | Transaction Set ID (850) |
| BEG | Beginning Segment | PO Type, PO Number, PO Date |
| CUR | Currency | Currency Code |
| REF | Reference Information | Reference IDs |
| DTM | Date/Time Reference | Delivery Date, Ship Date |
| N1 | Party Identification | BY=Buyer, ST=Ship To, SE=Seller |
| N3 | Address Information | Street Address |
| N4 | Geographic Location | City, State, ZIP, Country |
| PER | Contact Information | Contact Name, Phone, Email |
| PO1 | Baseline Item Data | Line #, Qty, Unit, Price, Product ID |
| PID | Product Description | Description Text |
| CTT | Transaction Totals | Line Item Count |
| AMT | Monetary Amount | Total Amount |
| SE | Transaction Set Trailer | Segment Count |
| GE | Functional Group Trailer | Transaction Count |
| IEA | Interchange Control Trailer | Group Count |

---

## 9. Testing Workflow

1. **Start Function Locally:**
   ```bash
   cd "Final Project/order-processing-function"
   func start
   ```

2. **Test X12 Mapping First:**
   ```bash
   curl -X POST "http://localhost:7071/api/x12-map" \
     -H "Content-Type: application/json" \
     -d '{"x12": "...", "transactionSet": "850", "includeMeta": true}'
   ```

3. **Test Full Order Processing:**
   ```bash
   curl -X POST "http://localhost:7071/api/process-order" \
     -H "Content-Type: application/json" \
     -d '{"x12": "...", "transactionSet": "850"}'
   ```

4. **Verify PostgreSQL:**
   ```sql
   SELECT * FROM orders ORDER BY created_at DESC LIMIT 5;
   SELECT * FROM order_items WHERE order_id = 'ORD-XXXXXXXX';
   ```

5. **Verify Blob Storage:**
   - Check Azure Portal > Storage Account > Containers > order-documents
   - Or use Azure Storage Explorer
