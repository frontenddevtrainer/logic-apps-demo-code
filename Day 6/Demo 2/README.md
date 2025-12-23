# Demo 2: Transforming Decoded JSON to Internal Order Format for API

## Overview
This demo builds on Demo 1 by transforming decoded X12 JSON into a normalized internal order format suitable for API consumption and integration with order management systems.

## Files in This Demo

### Logic App Workflow
- **[LogicApp_X12_to_Internal_Order_Format.json](LogicApp_X12_to_Internal_Order_Format.json)** - Main workflow definition

## Required Setup

### 1. Integration Account Setup
Same as Demo 1:
- Upload schema: `../Schemas/X12_00401_850.xsd`
- Create agreement: `ContosoRetail_To_FabrikamSupplies_X12`

### 2. Logic App Connections

#### X12 Connection
Same as Demo 1 - X12 connector for decoding

### 3. API Endpoint Configuration

Update the `Send_to_Order_API` action with your actual Order Management API endpoint:
```json
"uri": "https://your-order-api.example.com/api/orders"
```

Add your API key as a parameter:
```json
"orderApiKey": {
  "type": "String",
  "value": "your-actual-api-key"
}
```

## Testing the Demo

### Test Data Files
Located in `../Sample Data/`:
- **sample_x12_850_purchase_order.x12** - Full X12 850 message
- **sample_request_demo1.json** - HTTP request body format (same format)
- **expected_internal_order_format.json** - Expected transformation output

### How to Test

1. **Deploy the Logic App** to Azure
2. **Configure API endpoint** (or use RequestBin for testing)
3. **Send POST request** with X12 message:
   ```json
   {
     "x12Message": "ISA*00*...[X12 message]...~"
   }
   ```

#### Example with RequestBin (for testing without real API):
1. Create a RequestBin at https://requestbin.com/
2. Update the `uri` in `Send_to_Order_API` action to your bin URL
3. Run the workflow
4. View the posted JSON in RequestBin

### Expected Transformation

Input: X12 850 EDI message
Output: Normalized JSON order format

```json
{
  "orderId": "PO-2023-12345",
  "orderType": "PurchaseOrder",
  "orderDate": "20231223",
  "requestedDeliveryDate": "20231230",
  "customer": {
    "customerId": "CONTOSORETAIL  ",
    "name": "Contoso Retail Corporation",
    "identifierCode": "92",
    "identifier": "12-3456789"
  },
  "supplier": {
    "supplierId": "FABRIKAMSUPPLY ",
    "name": "Contoso Warehouse District 5"
  },
  "lineItems": [
    {
      "lineNumber": "1",
      "quantity": 100,
      "unitOfMeasure": "EA",
      "unitPrice": 29.99,
      "productId": "043000181706",
      "productIdQualifier": "UP",
      "productDescription": "Premium Alpha Widget - 500 Series",
      "lineTotal": 2999.00
    }
  ],
  "totalAmount": 11596.50,
  "currency": "USD",
  "status": "pending",
  "metadata": {
    "receivedAt": "2023-12-23T14:30:00Z",
    "source": "X12_EDI",
    "interchangeControlNumber": "000000001",
    "functionalGroupControlNumber": "1",
    "transactionSetControlNumber": "0001"
  }
}
```

## Workflow Actions Explained

1. **Decode X12 Message** - Parse incoming EDI message
2. **Parse Decoded X12** - Extract transaction data
3. **Transform to Internal Format** - Map X12 fields to internal schema
4. **Initialize Variables** - Setup arrays and counters for processing
5. **Process Each LineItem** - Loop through PO1 segments:
   - Calculate line totals (quantity × unit price)
   - Format line item with all product details
   - Append to processed items array
   - Update running total
6. **Build Final Order Object** - Combine all data into final structure
7. **Send to Order API** - HTTP POST to internal system
8. **Response** - Return confirmation with order details

## Data Transformation Mapping

### Header Mapping

| X12 Field | Internal Field | Description |
|-----------|----------------|-------------|
| BEG03 | orderId | Purchase Order Number |
| BEG05 | orderDate | Order Date (YYYYMMDD) |
| DTM02 (DTM01='002') | requestedDeliveryDate | Delivery Date |
| ISA06 | customer.customerId | Sender ID |
| N1Loop[0].N102 (N101='BY') | customer.name | Buyer Name |
| N1Loop[0].N104 | customer.identifier | Tax ID / DUNS |
| ISA08 | supplier.supplierId | Receiver ID |

### Line Item Mapping

| X12 Field | Internal Field | Description |
|-----------|----------------|-------------|
| PO101 | lineNumber | Line sequence number |
| PO102 | quantity | Quantity ordered |
| PO103 | unitOfMeasure | Unit (EA, CS, etc.) |
| PO104 | unitPrice | Price per unit |
| PO107 | productId | UPC/Product code |
| PO106 | productIdQualifier | ID type (UP, BP, etc.) |
| PID05 | productDescription | Product name |
| (calculated) | lineTotal | quantity × unitPrice |

## Business Logic

### Line Total Calculation
```
lineTotal = quantity × unitPrice
```

### Order Total Calculation
```
totalAmount = Σ(all line totals)
```

### Status Assignment
- New orders from EDI: `"pending"`
- Awaiting internal approval/processing

## API Integration

### Request Format
```http
POST /api/orders HTTP/1.1
Host: your-order-api.example.com
Content-Type: application/json
X-API-Key: your-api-key
X-Correlation-Id: {generated-guid}

{
  "orderId": "PO-2023-12345",
  ...
}
```

### Expected API Response
```json
{
  "status": "created",
  "orderId": "PO-2023-12345",
  "internalOrderId": "ORD-987654",
  "message": "Order successfully created"
}
```

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify API endpoint URL is correct
   - Check API key is valid
   - Ensure API accepts JSON content-type
   - Check firewall/network allows Logic App IP ranges

2. **Calculation Errors**
   - Ensure PO102 (quantity) and PO104 (price) are valid numbers
   - Use `float()` function for decimal conversions
   - Handle empty or missing values with default values

3. **Missing Line Item Data**
   - Not all X12 messages include PID segments
   - Use safe navigation: `?['PID']?[0]?['PID05']`
   - Provide fallback values for optional fields

4. **Array Processing Issues**
   - PO1Loop is an array, even with one item
   - Use ForEach loop for proper iteration
   - Initialize arrays before appending

## Best Practices

1. **Error Handling**
   - Add try-catch scopes around API calls
   - Log failures to blob storage or Application Insights
   - Implement retry policies for transient failures

2. **Data Validation**
   - Validate required fields exist before transformation
   - Check data types match expected format
   - Implement business rule validations

3. **Performance**
   - Use parallel processing where possible
   - Batch API calls if processing multiple orders
   - Consider async patterns for long-running operations

4. **Security**
   - Store API keys in Key Vault
   - Use managed identities for authentication
   - Encrypt sensitive data in transit and at rest

## Next Steps

- **Demo 3**: Generate 997 Functional Acknowledgment
- **Demo 4**: Complete end-to-end B2B workflow with all components

## Additional Resources

- [Logic Apps ForEach Loop](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-control-flow-loops)
- [Expression Functions Reference](https://learn.microsoft.com/en-us/azure/logic-apps/workflow-definition-language-functions-reference)
- [HTTP Action in Logic Apps](https://learn.microsoft.com/en-us/azure/connectors/connectors-native-http)
