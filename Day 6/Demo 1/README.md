# Demo 1: Logic App Decoding X12 850 to JSON with All Segments

## Overview
This demo demonstrates decoding an X12 850 Purchase Order message into JSON format with all segments extracted and organized for easy consumption.

## Files in This Demo

### Logic App Workflow
- **[LogicApp_X12_Decode_to_JSON.json](LogicApp_X12_Decode_to_JSON.json)** - Main workflow definition

## Required Setup

### 1. Integration Account Setup

#### Upload Schema to Integration Account
1. Navigate to your **Integration Account** in Azure Portal
2. Go to **Schemas** section
3. Click **+ Add**
4. Upload: `../Schemas/X12_00401_850.xsd`
5. Name: `X12_00401_850`

#### Create X12 Agreement
1. Navigate to your **Integration Account** > **Agreements**
2. Click **+ Add**
3. Configure the agreement:
   - **Name**: `ContosoRetail_To_FabrikamSupplies_X12`
   - **Agreement Type**: X12
   - **Host Partner**: FabrikamSupplies (Receiver)
   - **Guest Partner**: ContosoRetail (Sender)
   - **Host Qualifier**: ZZ
   - **Host Identifier**: FABRIKAMSUPPLY
   - **Guest Qualifier**: ZZ
   - **Guest Identifier**: CONTOSORETAIL
   - **Receive Settings**: Enable default settings
   - **Send Settings**: Configure as needed

### 2. Logic App Connections

#### X12 Connection
1. Create or use existing X12 connector connection
2. Update the workflow parameters section with your connection details:
   ```json
   "x12": {
     "id": "/subscriptions/{subscription-id}/providers/Microsoft.Web/locations/{location}/managedApis/x12",
     "connectionId": "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/connections/x12",
     "connectionName": "x12"
   }
   ```

## Testing the Demo

### Test Data Files
Located in `../Sample Data/`:
- **sample_x12_850_purchase_order.x12** - Full X12 850 message with 3 line items
- **sample_x12_850_simple.x12** - Simple X12 850 message for basic testing
- **sample_request_demo1.json** - HTTP request body format

### How to Test

#### Option 1: Using HTTP Request Tool (Postman, cURL, etc.)

1. **Deploy the Logic App** to Azure
2. **Get the HTTP POST URL** from the Logic App trigger
3. **Send POST request** with body:
   ```json
   {
     "x12Message": "ISA*00*          *00*          *ZZ*CONTOSORETAIL  *ZZ*FABRIKAMSUPPLY *231223*1430*U*00401*000000001*0*P*:~GS*PO*CONTOSORETAIL*FABRIKAMSUPPLY*20231223*1430*1*X*004010~ST*850*0001~BEG*00*NE*PO-2023-12345**20231223~..."
   }
   ```

#### Example cURL Command:
```bash
curl -X POST "https://{your-logic-app-url}" \
  -H "Content-Type: application/json" \
  -d @../Sample\ Data/sample_request_demo1.json
```

#### Option 2: Using Logic App Designer Test Feature

1. Open Logic App in Azure Portal
2. Click **Run Trigger** > **Run with payload**
3. Paste content from `sample_request_demo1.json`
4. Click **Run**

### Expected Response

The workflow returns a JSON response similar to `../Sample Data/expected_decoded_json_output.json`:

```json
{
  "status": "decoded",
  "timestamp": "2023-12-23T14:30:00Z",
  "messageType": "X12_850_PurchaseOrder",
  "allSegments": {
    "ISA_InterchangeControlHeader": { ... },
    "GS_FunctionalGroupHeader": { ... },
    "ST_TransactionSetHeader": { ... },
    "BEG_BeginningSegment": { ... },
    "REF_ReferenceIdentification": [ ... ],
    "DTM_DateTimeReference": [ ... ],
    "N1_Name": [ ... ],
    "PO1_BaselineItemData": [ ... ],
    "CTT_TransactionTotals": { ... }
  },
  "summary": {
    "purchaseOrderNumber": "PO-2023-12345",
    "orderDate": "20231223",
    "sender": "CONTOSORETAIL  ",
    "receiver": "FABRIKAMSUPPLY ",
    "lineItemCount": 3
  }
}
```

## Workflow Actions Explained

1. **Manual Trigger (HTTP Request)**
   - Accepts POST requests with X12 message in body
   - Schema validation for `x12Message` property

2. **Decode X12 Message**
   - Uses Integration Account X12 connector
   - Automatically parses X12 850 format using agreement

3. **Parse X12 Decoded JSON**
   - Parses the decoded output for easy access
   - Extracts ISA, GS, ST, and TransactionSets

4. **Extract All Segments**
   - Compose action to organize all EDI segments
   - Maps segments to descriptive property names:
     - ISA → Interchange Control Header
     - GS → Functional Group Header
     - ST → Transaction Set Header
     - BEG → Beginning Segment for Purchase Order
     - REF → Reference Identification
     - DTM → Date/Time Reference
     - N1Loop → Name/Party Identification Loop
     - PO1Loop → Baseline Item Data Loop
     - CTT → Transaction Totals
     - SE/GE/IEA → Trailer Segments

5. **Format Response JSON**
   - Creates structured response with:
     - Processing status and timestamp
     - All extracted segments
     - Summary information (PO#, date, parties, item count)

6. **Response**
   - Returns HTTP 200 with formatted JSON
   - Content-Type: application/json

## Understanding X12 850 Segments

### Key Segments in the Response

| Segment | Description | Example Data |
|---------|-------------|--------------|
| **ISA** | Interchange Control Header | Sender/Receiver IDs, Control Numbers |
| **GS** | Functional Group Header | Application sender/receiver, timestamp |
| **ST** | Transaction Set Header | Document type (850), control number |
| **BEG** | Beginning Segment | PO Number (BEG03), PO Date (BEG05) |
| **REF** | Reference Numbers | Department, Internal Order references |
| **DTM** | Date/Time References | Delivery date, Order date |
| **N1** | Party Identification | Buyer (BY), Ship-To (ST) with addresses |
| **PO1** | Purchase Order Line Item | Qty, Price, Product ID, UPC |
| **PID** | Product Description | Human-readable product names |
| **CTT** | Transaction Totals | Total line items, total quantity |

### Sample Data Breakdown

Using `sample_x12_850_purchase_order.x12`:

- **Purchase Order**: PO-2023-12345
- **Order Date**: 2023-12-23
- **Delivery Date**: 2023-12-30
- **Buyer**: Contoso Retail Corporation
- **Ship-To**: Contoso Warehouse District 5
- **Line Items**: 3 products
  1. 100 EA × $29.99 - Premium Alpha Widget
  2. 50 EA × $149.99 - Beta Gadget Pro
  3. 200 EA × $5.49 - Gamma Supply Kit

## Troubleshooting

### Common Issues

1. **"Agreement not found" Error**
   - Verify agreement name matches: `ContosoRetail_To_FabrikamSupplies_X12`
   - Check sender/receiver qualifiers and identifiers in ISA segment

2. **Schema Validation Errors**
   - Ensure X12_00401_850 schema is uploaded to Integration Account
   - Verify X12 message format matches schema version (00401)

3. **Decode Fails**
   - Check ISA segment format (proper delimiters: *, ~)
   - Verify segment terminator is ~ (tilde)
   - Ensure element separator is * (asterisk)

4. **Missing Segments in Output**
   - Optional segments may not appear in all messages
   - Use safe navigation operators `?['property']` in expressions

## Next Steps

- **Demo 2**: Transform decoded JSON to internal order format for API integration
- **Demo 3**: Generate 997 Functional Acknowledgment
- **Demo 4**: Complete end-to-end B2B workflow

## Additional Resources

- [X12 850 Purchase Order Specification](https://www.stedi.com/edi/x12-004010/850)
- [Azure Logic Apps X12 Connector Documentation](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-enterprise-integration-x12)
- [Integration Account Setup Guide](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-enterprise-integration-create-integration-account)
