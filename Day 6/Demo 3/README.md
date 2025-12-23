# Demo 3: Generating 997 Acknowledgment for Received X12 Message

## Overview
This demo demonstrates automatic generation of X12 997 Functional Acknowledgment in response to received EDI messages, which is critical for B2B EDI compliance.

## Files in This Demo

### Logic App Workflow
- **[LogicApp_Generate_997_Acknowledgment.json](LogicApp_Generate_997_Acknowledgment.json)** - Main workflow definition

## Required Setup

### 1. Integration Account Setup

#### Upload Schemas
1. **X12 850 Schema** (for incoming messages):
   - Upload: `../Schemas/X12_00401_850.xsd`
   - Name: `X12_00401_850`

2. **X12 997 Schema** (for acknowledgments):
   - Upload: `../Schemas/X12_00401_997.xsd`
   - Name: `X12_00401_997`

#### Create X12 Agreements

1. **Receive Agreement** (for decoding 850):
   - Name: `ContosoRetail_To_FabrikamSupplies_X12`
   - Host Partner: FabrikamSupplies (you/receiver)
   - Guest Partner: ContosoRetail (trading partner/sender)

2. **Send Agreement** (for encoding 997):
   - Name: `FabrikamSupplies_To_ContosoRetail_X12_997`
   - Host Partner: FabrikamSupplies (you/sender)
   - Guest Partner: ContosoRetail (trading partner/receiver)
   - Transaction Set: 997 - Functional Acknowledgment

### 2. Logic App Connections

#### X12 Connection
Same as previous demos - X12 connector for encoding/decoding

## Testing the Demo

### Test Data Files
Located in `../Sample Data/`:
- **sample_x12_850_purchase_order.x12** - Input X12 850 message
- **sample_request_demo1.json** - HTTP request body format
- **expected_997_acknowledgment.x12** - Expected 997 output

### How to Test

1. **Deploy the Logic App** to Azure
2. **Send POST request** with X12 850 message:
   ```json
   {
     "x12Message": "ISA*00*...[X12 850 message]...~"
   }
   ```

### Expected Response

```json
{
  "acknowledgmentStatus": "generated",
  "acknowledgmentType": "997_FunctionalAcknowledgment",
  "timestamp": "2023-12-23T14:31:00Z",
  "originalMessage": {
    "interchangeControlNumber": "000000001",
    "functionalGroupControlNumber": "1",
    "transactionSetControlNumber": "0001",
    "senderId": "CONTOSORETAIL  ",
    "receiverId": "FABRIKAMSUPPLY "
  },
  "acknowledgmentStatus": {
    "code": "A",
    "description": "Accepted"
  },
  "x12_997_Message": "ISA*00*...[997 acknowledgment]...~"
}
```

## Workflow Actions Explained

1. **Decode X12 Message** - Parse incoming 850
2. **Parse Decoded Message** - Extract control information
3. **Extract Control Numbers** - Get ISA13, GS06, ST02 for reference
4. **Build 997 Acknowledgment XML** - Create compliant 997 structure
5. **Encode 997 to X12** - Convert XML to X12 format using agreement
6. **Format 997 Response** - Package acknowledgment with metadata
7. **Response** - Return 997 message and status

## Understanding X12 997 Acknowledgment

### Purpose
The 997 Functional Acknowledgment:
- Confirms receipt of EDI transmission
- Reports syntax errors if found
- Required for most EDI trading partner agreements
- Provides audit trail for compliance

### 997 Structure

```
ISA - Interchange Control Header (reversed sender/receiver)
  GS - Functional Group Header (FA = Functional Acknowledgment)
    ST - Transaction Set Header (997)
      AK1 - Functional Group Response Header
      AK2 - Transaction Set Response Header
        AK5 - Transaction Set Response Trailer (status code)
      AK9 - Functional Group Response Trailer
    SE - Transaction Set Trailer
  GE - Functional Group Trailer
IEA - Interchange Control Trailer
```

### Key 997 Segments

| Segment | Element | Description | Value |
|---------|---------|-------------|-------|
| **AK1** | AK101 | Functional ID Code | "PO" (from original GS01) |
| | AK102 | Group Control Number | From original GS06 |
| **AK2** | AK201 | Transaction Set ID | "850" (from original ST01) |
| | AK202 | Transaction Control Number | From original ST02 |
| **AK5** | AK501 | Transaction Set Ack Code | "A" = Accepted |
| **AK9** | AK901 | Functional Group Ack Code | "A" = Accepted |
| | AK902 | Number of Sets Included | Count of transaction sets |
| | AK903 | Number of Sets Received | Count received |
| | AK904 | Number of Sets Accepted | Count accepted |

### Acknowledgment Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| **A** | Accepted | Transaction set accepted with no errors |
| **E** | Accepted with Errors | Non-fatal errors found |
| **R** | Rejected | Fatal errors, transaction rejected |
| **P** | Partially Accepted | Some transaction sets rejected |

## XML Structure for 997

The workflow builds this XML structure:

```xml
<X12Interchange xmlns="http://schemas.microsoft.com/BizTalk/EDI/X12/2006">
  <ISA>
    <!-- Sender/Receiver reversed from original -->
    <ISA06>{original receiver}</ISA06>
    <ISA08>{original sender}</ISA08>
    <ISA13>{same interchange control number}</ISA13>
  </ISA>
  <FunctionalGroup>
    <GS>
      <GS01>FA</GS01> <!-- Functional Acknowledgment -->
      <GS06>{group control number}</GS06>
    </GS>
    <TransactionSet>
      <ST>
        <ST01>997</ST01>
      </ST>
      <AK1>
        <AK101>PO</AK101>
        <AK102>{from original GS06}</AK102>
      </AK1>
      <AK2Loop1>
        <AK2>
          <AK201>850</AK201>
          <AK202>{from original ST02}</AK202>
        </AK2>
        <AK5>
          <AK501>A</AK501> <!-- Accepted -->
        </AK5>
      </AK2Loop1>
      <AK9>
        <AK901>A</AK901> <!-- Accepted -->
        <AK902>1</AK902>
        <AK903>1</AK903>
        <AK904>1</AK904>
      </AK9>
    </TransactionSet>
  </FunctionalGroup>
</X12Interchange>
```

## Control Number Handling

### Important Rules
1. **ISA13** (Interchange Control Number):
   - Use SAME number as original message
   - This links acknowledgment to original

2. **GS06** (Functional Group Control Number):
   - Referenced in AK102
   - Can be same as original or new

3. **ST02** (Transaction Set Control Number):
   - Referenced in AK202
   - 997 gets its own ST02 (usually "0001")

## Compliance Requirements

### EDI Trading Partner Agreements Usually Require:
- 997 acknowledgment within specific timeframe (e.g., 24 hours)
- Acknowledgment for EVERY received transaction
- Proper error reporting if validation fails
- Retention of 997s for audit (typically 7 years)

### Best Practices:
1. Send 997 even if transaction is rejected
2. Log all 997s sent/received
3. Match 997s to original transactions using control numbers
4. Implement timeout monitoring for missing 997s

## Troubleshooting

### Common Issues

1. **Agreement Not Found**
   - Verify both receive and send agreements exist
   - Check agreement names match workflow
   - Confirm partner identifiers are correct

2. **Invalid Control Numbers**
   - Ensure control numbers are extracted correctly
   - Verify they match original message
   - Check for leading/trailing spaces

3. **997 Encoding Fails**
   - Validate XML structure matches schema
   - Check namespace is correct
   - Ensure all required segments are present

4. **Trading Partner Rejects 997**
   - Verify sender/receiver IDs are reversed correctly
   - Check ISA/GS qualifiers match agreement
   - Validate control numbers reference original

## Integration with Production Workflows

In Demo 4, you'll see how to:
- Automatically send 997 to trading partner via HTTP/SFTP
- Store 997 for compliance/audit
- Link 997 to original transaction in database
- Handle 997 errors and retries

## Next Steps

- **Demo 4**: Complete end-to-end B2B workflow integrating all components

## Additional Resources

- [X12 997 Specification](https://www.stedi.com/edi/x12-004010/997)
- [EDI Acknowledgment Best Practices](https://www.edibasics.com/edi-resources/997-functional-acknowledgment/)
- [Azure Integration Account Agreements](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-enterprise-integration-agreements)
