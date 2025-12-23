# Demo 4: XML Validation & Error Handling for X12 850

## Overview
This demo enhances the Demo 3 workflow by adding XML validation and comprehensive error handling. It ensures the transformed X12 850 XML conforms to the schema before encoding, providing early detection of data quality issues and proper error routing.

## What This Demo Adds
1. **XML Schema Validation** - Validates transformed XML against X12 850 schema
2. **Conditional Logic** - Routes valid vs. invalid documents differently
3. **Error Handling** - Captures validation errors and returns appropriate responses
4. **Quality Gates** - Prevents invalid data from being encoded to X12

## Architecture Flow
```
[HTTP POST] → [Flat File Decode] → [Transform XML] → [Validate XML] → [Condition]
   (CSV)                                                                    ↓
                                                              ┌─────────────┴──────────────┐
                                                              ↓                            ↓
                                                         [Valid Path]              [Invalid Path]
                                                              ↓                            ↓
                                                    [X12 Encode]                  [Error Response]
                                                              ↓                     (HTTP 400)
                                                    [HTTP Response]
                                                     (HTTP 200)
```

## Prerequisites Checklist

### From Previous Demos
- ✅ **Demo 3 Workflow** - Working CSV to X12 850 Logic App
- ✅ **Integration Account** with:
  - Partners: ContosoRetail, FabrikamSupplies
  - Agreement: `ContosoRetail_To_FabrikamSupplies_X12`
  - Schema: `orders-flatfile` (CSV schema from `Day 5/schemas/orders-flatfile.xsd`)
  - Map: `CsvToX12_850` (XSLT transformation from `Day 5/schemas/CsvToX12_850.xslt`)

### New Requirements for Demo 4
- ✅ **X12 850 XML Schema** - Upload `Day 5/schemas/X12_00401_850.xsd` to Integration Account
  - This schema defines the valid structure for X12 850 XML (before encoding to EDI)
  - Used by the Validate XML action
  - **IMPORTANT**: Ensure the XSLT map uses correct element names (`N1Loop`, `PO1Loop`) that match this schema

### Azure Resources
- ✅ Integration Account (from Demo 1)
- ✅ Logic App with Demo 3 workflow
- ✅ X12 API Connection (from Demo 3)

## Cost Considerations
- **No Additional Costs** - XML validation uses the Integration Account you already have
- **No Extra Connectors** - All actions use built-in Logic Apps capabilities
- **Consumption Tier** - Pay only for workflow executions

## Step-by-Step Implementation

### Step 1: Upload X12 850 XML Schema

1. **Navigate to Integration Account**
   ```
   Azure Portal → Your Integration Account → Schemas
   ```

2. **Upload X12 850 Schema**
   - Click **+ Add**
   - Name: `X12_00401_850` (or `X12_850_PurchaseOrder`)
   - Schema Type: `EDI` or `XML`
   - File: Upload `Day 5/schemas/X12_00401_850.xsd`
   - Click **OK**

3. **Update XSLT Map (CRITICAL)**
   - Navigate to **Maps** in Integration Account
   - Update or re-upload the `CsvToX12_850` map
   - File: Upload the corrected `Day 5/schemas/CsvToX12_850.xslt`
   - This version uses correct element names (`N1Loop`, `PO1Loop`) that match the schema
   - **Without this update, validation will fail**

4. **Verify Schema Upload**
   - Confirm schema appears in the list
   - Check that the namespace matches: `http://schemas.microsoft.com/BizTalk/EDI/X12/2006`

### Step 2: Modify the Demo 3 Workflow

#### Starting Point: Demo 3 Workflow Structure
```
1. HTTP Trigger (manual)
2. Flat_File_Decoding
3. Transform_XML
4. Encode_to_X12_message_by_agreement_name_(V2)
5. Response
```

#### Target: Demo 4 Enhanced Workflow Structure
```
1. HTTP Trigger (manual)
2. Flat_File_Decoding
3. Transform_XML
4. Validate_XML (NEW)
5. Condition (NEW)
   ├─ True Branch:
   │  ├─ Encode_to_X12_message_by_agreement_name_(V2)
   │  └─ Response (200 OK with X12 message)
   └─ False Branch:
      └─ Response (400 Bad Request with validation errors)
```

### Step 3: Add XML Validation Action

**Insert after Transform_XML, before Encode_to_X12:**

1. **Add Action: XML Validation**
   - Action: `XML Validation`
   - Content: `@body('Transform_XML')`
   - Schema Name: `X12_00401_850`
   - This validates the transformed XML against the X12 850 schema

2. **What This Validates**
   - Required elements are present (ST, BEG, N1, PO1, SE segments)
   - Data types are correct (strings, dates, numbers)
   - Element order follows X12 850 specification
   - Cardinality rules (min/max occurrences)
   - Value constraints and patterns

### Step 4: Add Condition for Validation Result

**Insert after Validate_XML:**

1. **Add Action: Condition**
   - Control action: `Condition`
   - Expression:
     ```
     @body('Validate_XML')?['IsValid']
     ```
   - This checks if XML validation passed

2. **Configure True Branch (Valid XML)**
   - Move the existing `Encode_to_X12_message_by_agreement_name_(V2)` action here
   - Move the existing `Response` action here
   - These actions only run when validation succeeds

3. **Configure False Branch (Invalid XML)**
   - Add new `Response` action
   - Status Code: `400`
   - Body:
     ```json
     {
       "error": "XML Validation Failed",
       "details": "@body('Validate_XML')?['Errors']",
       "timestamp": "@utcNow()",
       "message": "The transformed X12 850 XML does not conform to the schema"
     }
     ```

### Step 5: Enhanced Error Response (Optional)

For more detailed error information, use this response body structure:

```json
{
  "status": "validation_failed",
  "errorCode": "X12_850_SCHEMA_VALIDATION_ERROR",
  "timestamp": "@utcNow()",
  "validationErrors": "@body('Validate_XML')?['Errors']",
  "inputFile": "CSV received via HTTP",
  "stage": "post_transformation",
  "suggestion": "Check CSV data quality and field mappings in CsvToX12_850 XSLT"
}
```

## Testing the Enhanced Workflow

### Test Case 1: Valid CSV Input (Happy Path)

**Input:** Valid `orders.csv` with complete data

**Expected Flow:**
1. ✅ HTTP POST received
2. ✅ CSV decoded to XML
3. ✅ XML transformed to X12 850 structure
4. ✅ XML validation passes (`IsValid: true`)
5. ✅ Condition evaluates to true branch
6. ✅ X12 encoding succeeds
7. ✅ HTTP 200 response with X12 850 message

**Test Command:**
```bash
curl -X POST "YOUR_LOGIC_APP_URL" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@orders.csv"
```

**Expected Response:**
- Status: 200 OK
- Body: X12 850 EDI message

### Test Case 2: Invalid CSV Input (Validation Failure)

**Input:** CSV with missing required fields or invalid data

**Examples of Invalid Data:**
- Missing OrderNumber (BEG03 required)
- Invalid OrderDate format (not CCYYMMDD)
- Missing BuyerId (N1 BY segment required)
- Invalid Quantity (must be numeric)

**Expected Flow:**
1. ✅ HTTP POST received
2. ✅ CSV decoded to XML
3. ✅ XML transformed (may produce incomplete X12 XML)
4. ❌ XML validation fails (`IsValid: false`)
5. ✅ Condition evaluates to false branch
6. ✅ HTTP 400 response with error details
7. 🚫 X12 encoding skipped (prevents invalid data)

**Test Command:**
```bash
curl -X POST "YOUR_LOGIC_APP_URL" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@orders-invalid.csv"
```

**Expected Response:**
- Status: 400 Bad Request
- Body: JSON with validation errors

### Test Case 3: Missing Required Segment

**Input:** CSV missing ShipToName (creates invalid N1 ST segment)

**Validation Error Example:**
```json
{
  "error": "XML Validation Failed",
  "details": [
    {
      "element": "N1/N102",
      "error": "Required element is missing",
      "xpath": "/X12_00401_850/N1Loop1[N101='ST']/N1/N102"
    }
  ],
  "timestamp": "2025-12-22T14:30:00Z",
  "message": "The transformed X12 850 XML does not conform to the schema"
}
```

## Understanding Validation Errors

### Common Validation Error Types

#### 1. Missing Required Elements
**Error Message:** "Required element is missing"
**Cause:** CSV missing data for mandatory X12 fields
**Solution:** Ensure CSV has values for all required columns
**Example:** Missing OrderNumber → BEG03 missing

#### 2. Invalid Data Type
**Error Message:** "The value does not match the expected data type"
**Cause:** Non-numeric value in quantity field, invalid date format
**Solution:** Validate CSV data types before submission
**Example:** Quantity = "ABC" instead of "100"

#### 3. Invalid Date Format
**Error Message:** "The value does not match the pattern"
**Cause:** Date not in CCYYMMDD format
**Solution:** Ensure dates are formatted as YYYYMMDD
**Example:** OrderDate = "12/22/2025" instead of "20251222"

#### 4. Cardinality Violation
**Error Message:** "Element occurs more/less than allowed"
**Cause:** Too many or too few repetitions of an element
**Solution:** Check XSLT map for-each loops and CSV data
**Example:** More than 999 PO1 line items

#### 5. Invalid Element Order
**Error Message:** "Element is out of sequence"
**Cause:** X12 segments in wrong order
**Solution:** Check XSLT map output structure
**Example:** PO1 segments before N1 segments

## Validation vs. Encoding

### Two Levels of Validation

| Stage | Action | Purpose | Detects |
|-------|--------|---------|---------|
| **Pre-Encoding** | XML Validation | Validate structure | Missing elements, wrong types, invalid structure |
| **During Encoding** | X12 Agreement Rules | Enforce EDI rules | Segment syntax, control numbers, delimiters |

### When to Use Each

**XML Validation (This Demo):**
- ✅ Better error messages (XML-level details)
- ✅ Fails fast before encoding overhead
- ✅ Easier to debug (XML path references)
- ✅ Prevents wasted X12 API calls
- ⚠️ Requires X12 XML schema in Integration Account

**Agreement Validation (Built-in):**
- ✅ Enforces partner-specific rules
- ✅ Validates EDI syntax and delimiters
- ✅ Checks control number sequences
- ✅ Always active during encoding
- ⚠️ Errors are EDI-specific (harder to trace to CSV)

**Best Practice:** Use both
1. XML Validation catches data quality issues early
2. Agreement Validation ensures EDI compliance

## Workflow Definition Reference

### Key Expression: Validation Check
```
@body('Validate_XML')?['IsValid']
```

This expression:
- Retrieves the `IsValid` property from validation output
- Returns `true` if XML conforms to schema
- Returns `false` if validation errors exist
- Uses `?[]` safe navigation to handle null values

### Validation Output Structure
```json
{
  "IsValid": true/false,
  "Errors": [
    {
      "Message": "Error description",
      "LineNumber": 42,
      "LinePosition": 15,
      "Details": "Additional context"
    }
  ]
}
```

### Complete Workflow Actions (Demo 4)
1. **manual** - HTTP Request trigger
2. **Flat_File_Decoding** - CSV to XML
3. **Transform_XML** - Apply CsvToX12_850 map
4. **Validate_XML** - Validate against X12_00401_850 schema
5. **Condition** - Check `IsValid`
   - **True Branch:**
     - **Encode_to_X12_message_by_agreement_name_(V2)** - Generate X12 EDI
     - **Response** - Return HTTP 200 with X12 message
   - **False Branch:**
     - **Response_2** - Return HTTP 400 with errors

## Advanced Error Handling Patterns

### Pattern 1: Log Validation Errors

Add action in False branch before Response:

**Action: Append to String Variable**
```
Variable: validationErrorLog
Value: @{concat(utcNow(), ' - ', body('Validate_XML')?['Errors'])}
```

### Pattern 2: Email Notification on Failure

Add action in False branch:

**Action: Send an email (V2)**
- To: `data-quality-team@company.com`
- Subject: `X12 Validation Failed - @{utcNow()}`
- Body:
  ```
  CSV to X12 transformation resulted in invalid XML.

  Validation Errors:
  @{body('Validate_XML')?['Errors']}

  Please review the CSV input data and XSLT mapping.
  ```

### Pattern 3: Store Invalid Data for Analysis

Add action in False branch:

**Action: Create blob (V2)**
- Folder path: `/validation-failures`
- Blob name: `invalid-@{utcNow()}.json`
- Blob content:
  ```json
  {
    "timestamp": "@{utcNow()}",
    "originalCsv": "@{triggerBody()['$multipart'][0]['body']}",
    "transformedXml": "@{body('Transform_XML')}",
    "validationErrors": "@{body('Validate_XML')?['Errors']}"
  }
  ```

### Pattern 4: Retry with Alternative Mapping

Add action in False branch:

**Action: Transform XML (alternative map)**
- Content: `@body('Flat_File_Decoding')`
- Map: `CsvToX12_850_Tolerant` (more lenient mapping)
- Then validate again and decide

## Troubleshooting Guide

### Issue 1: "Schema not found" Error
**Symptoms:** Validate XML action fails with schema error
**Solution:**
- Verify `X12_00401_850` (or `X12_850_PurchaseOrder`) schema is uploaded to Integration Account
- Check schema name in Validate_XML action matches the uploaded schema name exactly (case-sensitive)
- Ensure Integration Account is linked to Logic App
- Validate schema type is set to EDI or XML

### Issue 0: Element Name Mismatch (MOST COMMON)
**Symptoms:** Validation fails with "Element not expected" or similar errors
**Root Cause:** XSLT generates `N1Loop1` and `PO1Loop1` but schema expects `N1Loop` and `PO1Loop`
**Solution:**
- Use the corrected XSLT from `Day 5/schemas/CsvToX12_850.xslt`
- This file has been updated to use correct element names without the "1" suffix
- Re-upload the map to Integration Account as `CsvToX12_850`
- The corrected XSLT also removes `PO108` and `PO109` elements not in the schema

### Issue 2: All Documents Fail Validation
**Symptoms:** Even known-good CSV files fail validation
**Solution:**
- Check XSLT map namespace matches schema namespace
- Verify `Transform_XML` output is actually X12 850 XML format
- Test XSLT map independently in Visual Studio
- Ensure schema version matches (00401, 00501, etc.)

### Issue 3: Validation Passes but Encoding Fails
**Symptoms:** `IsValid: true` but X12 encode action fails
**Solution:**
- XML schema validation checks structure, not all EDI rules
- Check agreement validation settings
- Verify partner identifiers match agreement
- Review control number configuration

### Issue 4: Cannot Access Validation Errors
**Symptoms:** `body('Validate_XML')?['Errors']` returns null
**Solution:**
- Use `body('Validate_XML')` to see full output structure
- Property name might be case-sensitive (`Errors` vs `errors`)
- Check if errors are nested: `body('Validate_XML')?['validationResult']?['errors']`
- Add default value: `coalesce(body('Validate_XML')?['Errors'], 'No error details available')`

### Issue 5: Performance Impact
**Symptoms:** Workflow takes significantly longer with validation
**Solution:**
- Validation adds 100-500ms per execution (acceptable for most scenarios)
- For high-volume scenarios (>1000/min), consider:
  - Async validation in separate workflow
  - Sampling (validate 10% of documents)
  - Caching validation results for similar documents

## Monitoring and Observability

### Key Metrics to Track

1. **Validation Success Rate**
   - Expression: `Count(where IsValid = true) / Total Count`
   - Target: >95%
   - Alert if: <90% for 5 consecutive runs

2. **Common Validation Errors**
   - Track error patterns in Application Insights
   - Identify data quality issues
   - Prioritize XSLT map improvements

3. **Response Time Impact**
   - Baseline: Demo 3 without validation
   - With validation: Should add <500ms
   - Alert if: >2s difference

### Application Insights Query

```kusto
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.LOGIC"
| where workflowName_s == "CSV_to_X12_with_Validation"
| extend ValidationResult = parse_json(properties_Validate_XML_outputs_s).IsValid
| summarize
    TotalRuns = count(),
    SuccessfulValidations = countif(ValidationResult == true),
    FailedValidations = countif(ValidationResult == false)
    by bin(TimeGenerated, 1h)
| project
    TimeGenerated,
    TotalRuns,
    SuccessfulValidations,
    FailedValidations,
    SuccessRate = round(SuccessfulValidations * 100.0 / TotalRuns, 2)
```