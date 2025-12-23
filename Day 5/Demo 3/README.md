# Demo 3: Logic App Workflow - CSV to X12 850 via HTTP

## Overview
This demo creates an end-to-end Azure Logic App workflow that:
1. Receives CSV purchase order files via HTTP POST
2. Decodes CSV to XML using flat file schema
3. Transforms XML using XSLT map
4. Encodes to X12 850 EDI format
5. Returns the X12 message in HTTP response

## Architecture Flow
```
[HTTP POST] → [Flat File Decode] → [XML Transform] → [X12 Encode] → [HTTP Response]
   (CSV)             ↓                    ↓                ↓           (X12 850)
                CSV Schema          XSLT Map        Agreement
              (orders-flatfile)   (CsvToX12_850)   (Demo 1)
```

## Prerequisites Checklist

### Azure Resources
- ✅ Integration Account (created in Demo 1)
- ✅ Logic App (Consumption or Standard tier)
- ✅ X12 API Connection (for encoding)

### Integration Account Assets
- ✅ **Partners** (from Demo 1):
  - ContosoRetail (Qualifier: ZZ, Value: BUYER01)
  - FabrikamSupplies (Qualifier: ZZ, Value: SELLER01)
  
- ✅ **Agreement** (from Demo 1):
  - Name: `ContosoRetail_To_FabrikamSupplies_X12`
  - Type: X12
  - Host Partner: ContosoRetail
  - Guest Partner: FabrikamSupplies

- ✅ **Schemas** (upload from `Day 5/schemas/`):
  1. `orders-flatfile.xsd` - CSV flat file schema
  2. `X12_00401_850.xsd` - X12 850 XML schema

- ✅ **Maps** (upload from `Day 5/schemas/`):
  - `CsvToX12_850.xslt` - Transformation map from CSV to X12 850

### Sample Files
- ✅ `orders.csv` - Sample input data
- ✅ `x12-850-sample.txt` - Expected output (for validation)

## Step-by-Step Implementation

### Step 1: Upload Schemas to Integration Account

1. **Navigate to Integration Account**
   ```
   Azure Portal → Your Integration Account → Schemas
   ```

2. **Upload CSV Schema**
   - Click **+ Add**
   - Name: `orders-flatfile`
   - Schema Type: `Other` (or `Flat File` if available)
   - File: Upload `Day 5/schemas/orders-flatfile.xsd`
   - Click **OK**

3. **Upload X12 Schema**
   - Click **+ Add**
   - Name: `X12_00401_850` (or `X12_850_PurchaseOrder`)
   - Schema Type: `EDI`
   - File: Upload `Day 5/schemas/X12_00401_850.xsd`
   - Click **OK**

### Step 2: Upload XSLT Map to Integration Account

1. **Navigate to Maps**
   ```
   Azure Portal → Your Integration Account → Maps
   ```

2. **Upload Map**
   - Click **+ Add**
   - Name: `CsvToX12_850`
   - Map Type: `XSLT`
   - File: Upload `Day 5/schemas/CsvToX12_850.xslt`
   - Click **OK**

### Step 3: Link Integration Account to Logic App

1. **Open your Logic App**
   ```
   Azure Portal → Your Logic App → Workflow settings
   ```

2. **Link Integration Account**
   - Under "Integration account", select your Integration Account
   - Click **Save**

### Step 4: Create the Logic App Workflow

#### 4.1: Add HTTP Trigger

1. **Create Trigger**
   - Trigger: `When a HTTP request is received`
   - Method: `POST`
   - The trigger will accept multipart/form-data with CSV file content

#### 4.2: Flat File Decode

2. **Add Action: Flat file decoding**
   - Action: `Flat file decoding`
   - Content: `@triggerBody()['$multipart'][0]['body']`
   - Schema Name: `orders-flatfile`
   - Output: XML representation of CSV data
   - **Note:** This extracts the first file from the multipart request

#### 4.3: Transform XML

3. **Add Action: Transform XML**
   - Action: `Transform XML`
   - Content: `@body('Flat_File_Decoding')`
   - Map: `CsvToX12_850`
   - Output: X12 850 XML structure

#### 4.4: Encode to X12

4. **Add Action: Encode to X12 message by agreement name (V2)**
   - Action: `Encode to X12 message by agreement name (V2)`
   - Message to encode: `@body('Transform_XML')`
   - Agreement name: `ContosoRetail_To_FabrikamSupplies_X12`
   - Connection: Use X12 API connection
   - Output: EDI X12 text format

#### 4.5: Return HTTP Response

5. **Add Action: Response**
   - Action: `Response`
   - Status Code: `200`
   - Body: `@body('Encode_to_X12_message_by_agreement_name_(V2)')`
   - This returns the generated X12 message directly to the caller

### Step 5: Test the Workflow

#### 5.1: Get the HTTP Endpoint URL

1. Save the Logic App workflow
2. Copy the HTTP POST URL from the trigger (appears after saving)
3. The URL will look like: `https://prod-XX.region.logic.azure.com:443/workflows/.../triggers/manual/paths/invoke?...`

#### 5.2: Send Test Request

Use a tool like Postman, curl, or PowerShell to send a POST request:

**Using curl:**
```bash
curl -X POST "YOUR_LOGIC_APP_URL" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@orders.csv"
```

**Using PowerShell:**
```powershell
$uri = "YOUR_LOGIC_APP_URL"
$filePath = "orders.csv"
$form = @{
    file = Get-Item -Path $filePath
}
Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

#### 5.3: Monitor Execution

1. Navigate to Logic App → Runs history
2. Click on the latest run
3. Expand each step to see:
   - ✅ HTTP request received
   - ✅ CSV decoded to XML
   - ✅ XML transformed to X12 structure
   - ✅ X12 message encoded
   - ✅ HTTP response sent

#### 5.4: Validate Output

1. The response body will contain the X12 850 message
2. Compare with expected `x12-850-sample.txt`
3. Verify structure:
   ```
   ISA*00*...*ZZ*BUYER01*...*ZZ*SELLER01*...~
   GS*PO*BUYER01*SELLER01*...~
   ST*850*0001~
   BEG*00*NE*PO2025001**20251222~
   N1*BY*ContosoRetail**92*BUYER01~
   N1*SE*FabrikamSupplies**92*SELLER01~
   N1*ST*Contoso Warehouse Seattle**92*SHIP001~
   N3*123 Main Street~
   N4*Seattle*WA*98101~
   PO1*1*100*EA*25.50**VP*WIDGET-001*PD*Blue Widget Standard Size~
   PO1*2*50*EA*15.75**VP*GADGET-200*PD*Red Gadget Deluxe Model~
   PO1*3*25*EA*42.00**VP*TOOL-350*PD*Green Tool Pro Edition~
   CTT*3~
   SE*13*0001~
   GE*1*1~
   IEA*1*000000001~
   ```

## Detailed Workflow Actions Reference

### Action 1: Flat File Decoding
**Purpose:** Convert CSV to XML

**Input (CSV):**
```csv
OrderNumber,OrderDate,BuyerId,BuyerName,...
PO2025001,20251222,BUYER01,ContosoRetail,...
```

**Output (XML):**
```xml
<Orders xmlns="http://schemas.logicapps.demo/orders/csv">
  <Order>
    <OrderNumber>PO2025001</OrderNumber>
    <OrderDate>20251222</OrderDate>
    <BuyerId>BUYER01</BuyerId>
    <BuyerName>ContosoRetail</BuyerName>
    ...
  </Order>
</Orders>
```

### Action 2: Transform XML
**Purpose:** Map CSV structure to X12 850 structure

**Input:** CSV XML (from Flat File Decode)
**Map:** CsvToX12_850 XSLT transformation
**Output:** X12 850 XML

```xml
<X12_00401_850 xmlns="http://schemas.microsoft.com/BizTalk/EDI/X12/2006">
  <ST>
    <ST01>850</ST01>
    <ST02>0001</ST02>
  </ST>
  <BEG>
    <BEG01>00</BEG01>
    <BEG02>NE</BEG02>
    <BEG03>PO2025001</BEG03>
    <BEG05>20251222</BEG05>
  </BEG>
  ...
</X12_00401_850>
```

### Action 3: Encode to X12
**Purpose:** Convert X12 XML to EDI text format

**Input:** X12 850 XML
**Agreement:** Provides delimiters, control numbers, party identifiers
**Output:** EDI X12 text

```
ISA*00*          *00*          *ZZ*BUYER01        *ZZ*SELLER01       *251222*1430*U*00401*000000001*0*T*:~
GS*PO*BUYER01*SELLER01*20251222*1430*1*X*00401~
ST*850*0001~
...
```

## Mapping Table (CSV → X12 850)

| CSV Field | X12 Segment | X12 Element | Description |
|-----------|-------------|-------------|-------------|
| OrderNumber | BEG | BEG03 | Purchase Order Number |
| OrderDate | BEG | BEG05 | Date (CCYYMMDD) |
| BuyerId | N1 (BY) | N104 | Buyer Identifier |
| BuyerName | N1 (BY) | N102 | Buyer Name |
| SellerId | N1 (SE) | N104 | Seller Identifier |
| SellerName | N1 (SE) | N102 | Seller Name |
| ShipToName | N1 (ST) | N102 | Ship To Name |
| ShipToId | N1 (ST) | N104 | Ship To Identifier |
| ShipToStreet | N3 (ST) | N301 | Address Line 1 |
| ShipToCity | N4 (ST) | N401 | City |
| ShipToState | N4 (ST) | N402 | State |
| ShipToPostal | N4 (ST) | N403 | Postal Code |
| LineNumber | PO1 | PO101 | Line Number |
| Quantity | PO1 | PO102 | Quantity |
| UOM | PO1 | PO103 | Unit of Measure |
| UnitPrice | PO1 | PO104 | Unit Price |
| ItemSku | PO1 | PO107 | Product/Service ID |
| ItemDescription | PO1 | PO109 | Product Description |

## Troubleshooting Guide

### Issue 1: "Schema not found"
**Symptoms:** Flat File Decode fails with schema error
**Solution:**
- Verify schema is uploaded to Integration Account
- Check schema name matches exactly (case-sensitive)
- Ensure Integration Account is linked to Logic App
- Verify schema type is set correctly

### Issue 2: "Invalid CSV format"
**Symptoms:** Flat File Decode fails or produces empty XML
**Solution:**
- Check CSV file has headers in first row
- Verify delimiter is comma (,)
- Ensure no extra blank lines at end
- Check for special characters or encoding issues
- Validate against orders-flatfile.xsd structure

### Issue 3: "Transform failed"
**Symptoms:** Transform XML action fails
**Solution:**
- Verify map is uploaded to Integration Account
- Check map name matches exactly
- Validate input XML structure matches source schema
- Test XSLT locally in Visual Studio first
- Check for namespace mismatches

### Issue 4: "X12 Encode failed"
**Symptoms:** Encode action fails with validation error
**Solution:**
- Verify agreement exists and is activated
- Check partner identifiers match (BUYER01, SELLER01)
- Ensure qualifiers are correct (ZZ)
- Validate X12 XML structure matches schema
- Check required segments are present (ST, BEG, PO1, SE)

### Issue 5: "Invalid X12 output"
**Symptoms:** X12 generated but doesn't validate
**Solution:**
- Check segment count in SE01
- Verify control numbers match (ST02 = SE02)
- Ensure proper segment terminators (~)
- Validate element separators (*)
- Check date formats (CCYYMMDD)

### Issue 6: "Missing line items"
**Symptoms:** X12 has header but no PO1 segments
**Solution:**
- Verify CSV has data rows (not just headers)
- Check XSLT for-each loop is correct
- Ensure CSV structure matches schema
- Validate multiple order lines in CSV

## Workflow Definition Reference

### Complete JSON Structure
The workflow consists of these key elements:

**Triggers:**
- `manual` - HTTP Request trigger that accepts POST requests

**Actions:**
1. `Flat_File_Decoding` - Decodes CSV from multipart request body
2. `Transform_XML` - Transforms CSV XML to X12 850 XML using XSLT map
3. `Encode_to_X12_message_by_agreement_name_(V2)` - Encodes X12 XML to EDI format
4. `Response` - Returns X12 message with HTTP 200 status

**Parameters:**
- `$connections` - Contains X12 API connection configuration

## Performance Optimization

### For High Volume Processing
1. **API Gateway:** Add Azure API Management in front for throttling and caching
2. **Async Processing:** Consider using Service Bus queue for fire-and-forget scenarios
3. **Parallel Processing:** Deploy multiple Logic App instances for load distribution
4. **Error Handling:** Add retry policies and exception handling

### Cost Optimization
1. **Use Consumption Tier:** Pay per execution (current setup)
2. **Connection Pooling:** Reuse X12 API connections
3. **Minimize Triggers:** Use batching in calling applications
4. **Monitor Usage:** Track action executions in Azure Monitor

## Testing Scenarios

### Test Case 1: Single Line Item
**Input:** CSV with 1 order line
**Expected:** X12 with 1 PO1 segment
**Validation:** SE01 segment count = 13

### Test Case 2: Multiple Line Items
**Input:** CSV with 3 order lines (provided sample)
**Expected:** X12 with 3 PO1 segments
**Validation:** SE01 segment count = 13, CTT01 = 3

### Test Case 3: Different Ship-To Address
**Input:** CSV with different ShipToCity/State
**Expected:** N4 segment reflects new address
**Validation:** N401, N402, N403 match CSV values

### Test Case 4: Special Characters in Description
**Input:** CSV with ItemDescription containing commas/quotes
**Expected:** Properly escaped in X12
**Validation:** No delimiter conflicts in X12 output

## What to Demonstrate Live

### Key Points to Highlight
1. **Integration Account Setup**
   - Show schemas, maps, agreements in one place
   - Explain reusability across multiple Logic Apps

2. **HTTP Trigger**
   - Show the HTTP endpoint URL
   - Explain multipart/form-data handling
   - Demonstrate how to extract file from request body

3. **Flat File Decoding**
   - Show CSV → XML transformation
   - Explain how schema defines structure
   - Show XML output in run history

4. **XSLT Transformation**
   - Explain mapping logic (CsvToX12_850)
   - Show how CSV fields map to X12 elements
   - Demonstrate XML → X12 XML transformation

5. **X12 Encoding**
   - Show how agreement provides envelope info
   - Explain control number management
   - Show final EDI text output

6. **End-to-End Flow**
   - Send HTTP POST with CSV file
   - Watch Logic App trigger in real-time
   - Step through each action in run history
   - Show X12 message in HTTP response

### Common Questions & Answers

**Q: Why use HTTP trigger instead of Blob Storage?**
A: HTTP triggers provide synchronous request-response pattern, useful for real-time integrations and API scenarios.

**Q: How do I handle errors?**
A: Add scope actions, configure run-after settings, and use error handling branches. Consider returning appropriate HTTP status codes (400, 500, etc.).

**Q: Can I process multiple files at once?**
A: The current implementation processes one file per request. For batch processing, modify the workflow to iterate through multiple files in the multipart request.

**Q: How are control numbers managed?**
A: The Integration Account automatically increments control numbers based on agreement settings (ISA13, GS06, ST02).

**Q: Can I customize the X12 format?**
A: Yes, modify the XSLT map (CsvToX12_850) or adjust agreement settings for delimiters and validation rules.

**Q: What if the calling application needs the X12 file instead of the message body?**
A: Modify the Response action to save to Blob Storage first, then return the blob URL or file name.

## Next Steps

### Extend the Demo
1. Add email notifications on success/failure
2. Implement logging to Azure Monitor
3. Add AS2 transport for secure transmission
4. Create 997 acknowledgment processing
5. Build reverse flow (X12 → CSV)

### Production Considerations
1. Implement proper error handling and retries
2. Add monitoring and alerting
3. Set up proper authentication and authorization
4. Configure backup and disaster recovery
5. Document partner-specific requirements
6. Establish operational procedures

## Resources

### Documentation
- [Azure Logic Apps Enterprise Integration](https://docs.microsoft.com/azure/logic-apps/logic-apps-enterprise-integration-overview)
- [X12 Message Encoding](https://docs.microsoft.com/azure/logic-apps/logic-apps-enterprise-integration-x12-encode)
- [Flat File Processing](https://docs.microsoft.com/azure/logic-apps/logic-apps-enterprise-integration-flatfile)

### Sample Files Location
- Input: `orders.csv`
- Expected Output: `x12-850-sample.txt`
- Schemas: `orders-flatfile.xsd`, `X12_850_PurchaseOrder.xsd`
- Map: `CsvToX12_850.xslt`
- Workflow: `LogicApp_CSV_to_X12_Workflow.json`
