# Day 6: X12 EDI Processing and B2B Integration Workflows

This folder contains four progressive demos showcasing X12 EDI message processing, transformation, and B2B integration workflows.

## Quick Start Guide

### Required Files Overview

| File Type | Location | Description | Required For |
|-----------|----------|-------------|--------------|
| **Schemas** | `/Schemas/` | X12 XSD schemas for Integration Account | All Demos |
| **Sample Data** | `/Sample Data/` | Test X12 messages and expected outputs | Testing |
| **Workflows** | `/Demo [1-4]/` | Logic App JSON definitions | Deployment |
| **Documentation** | `/Demo [1-4]/README.md` | Detailed setup and testing guides | Reference |

### File Structure

```
Day 6/
├── README.md                          # This file
├── Schemas/                           # Integration Account Schemas
│   ├── X12_00401_850.xsd             # Purchase Order schema
│   └── X12_00401_997.xsd             # Functional Acknowledgment schema
├── Sample Data/                       # Test Files
│   ├── sample_x12_850_purchase_order.x12      # Full test message
│   ├── sample_x12_850_simple.x12              # Simple test message
│   ├── sample_request_demo1.json              # HTTP request format
│   ├── expected_decoded_json_output.json      # Demo 1 output
│   ├── expected_internal_order_format.json    # Demo 2 output
│   └── expected_997_acknowledgment.x12        # Demo 3 output
├── Demo 1/                            # X12 Decoding
│   ├── LogicApp_X12_Decode_to_JSON.json
│   └── README.md
├── Demo 2/                            # Transformation to Internal Format
│   ├── LogicApp_X12_to_Internal_Order_Format.json
│   └── README.md
├── Demo 3/                            # 997 Acknowledgment Generation
│   ├── LogicApp_Generate_997_Acknowledgment.json
│   └── README.md
└── Demo 4/                            # Complete B2B Workflow
    ├── LogicApp_Complete_B2B_Workflow.json
    └── README.md
```

### Setup Prerequisites

Before running any demo, you need:

1. **Azure Integration Account**
   - Upload schemas from `/Schemas/` folder
   - Create X12 trading partner agreements
   - Link to Logic App

2. **Azure Blob Storage** (Demo 4 only)
   - Create folder structure for file processing
   - Configure connection in Logic App

3. **Sample Data**
   - Use files from `/Sample Data/` for testing
   - Modify as needed for your scenarios

## Required Schemas

### X12_00401_850.xsd - Purchase Order Schema
**Location:** [Schemas/X12_00401_850.xsd](Schemas/X12_00401_850.xsd)

**Purpose:** Validates and structures incoming X12 850 Purchase Orders

**Upload to Integration Account:**
1. Navigate to Integration Account → Schemas
2. Click "+ Add"
3. Upload `X12_00401_850.xsd`
4. Name: `X12_00401_850`

### X12_00401_997.xsd - Functional Acknowledgment Schema
**Location:** [Schemas/X12_00401_997.xsd](Schemas/X12_00401_997.xsd)

**Purpose:** Validates and structures outgoing X12 997 Acknowledgments

**Upload to Integration Account:**
1. Navigate to Integration Account → Schemas
2. Click "+ Add"
3. Upload `X12_00401_997.xsd`
4. Name: `X12_00401_997`

## Sample Data Files

### Test X12 Messages

#### sample_x12_850_purchase_order.x12
**Location:** [Sample Data/sample_x12_850_purchase_order.x12](Sample Data/sample_x12_850_purchase_order.x12)

**Description:** Complete X12 850 Purchase Order with 3 line items
- Purchase Order: PO-2023-12345
- Buyer: Contoso Retail Corporation
- Supplier: Fabrikam Supplies
- 3 Product lines totaling $11,596.50

**Use In:** All Demos

#### sample_x12_850_simple.x12
**Location:** [Sample Data/sample_x12_850_simple.x12](Sample Data/sample_x12_850_simple.x12)

**Description:** Minimal X12 850 for basic testing
- Purchase Order: PO-TEST-001
- 1 Product line
- Simplified structure for troubleshooting

**Use In:** Initial testing, troubleshooting

### HTTP Request Format

#### sample_request_demo1.json
**Location:** [Sample Data/sample_request_demo1.json](Sample Data/sample_request_demo1.json)

**Description:** HTTP POST body format for Demos 1, 2, and 3

**Usage:**
```bash
curl -X POST "https://{logic-app-url}" \
  -H "Content-Type: application/json" \
  -d @"Sample Data/sample_request_demo1.json"
```

### Expected Outputs

#### expected_decoded_json_output.json
**Location:** [Sample Data/expected_decoded_json_output.json](Sample Data/expected_decoded_json_output.json)

**Demo:** 1
**Description:** Complete decoded X12 structure with all segments

#### expected_internal_order_format.json
**Location:** [Sample Data/expected_internal_order_format.json](Sample Data/expected_internal_order_format.json)

**Demo:** 2
**Description:** Transformed order in internal API format with calculated totals

#### expected_997_acknowledgment.x12
**Location:** [Sample Data/expected_997_acknowledgment.x12](Sample Data/expected_997_acknowledgment.x12)

**Demo:** 3
**Description:** Generated 997 Functional Acknowledgment in X12 format

## Integration Account Configuration

### Required X12 Agreements

#### Agreement 1: Receive 850 Purchase Orders
- **Name:** `ContosoRetail_To_FabrikamSupplies_X12`
- **Type:** X12
- **Direction:** Receive
- **Host Partner:** FabrikamSupplies (You)
- **Guest Partner:** ContosoRetail (Trading Partner)
- **Host Qualifier:** ZZ
- **Host Value:** FABRIKAMSUPPLY
- **Guest Qualifier:** ZZ
- **Guest Value:** CONTOSORETAIL
- **Transaction Sets:** 850
- **Used In:** All Demos

#### Agreement 2: Send 997 Acknowledgments
- **Name:** `FabrikamSupplies_To_ContosoRetail_X12_997`
- **Type:** X12
- **Direction:** Send
- **Host Partner:** FabrikamSupplies (You)
- **Guest Partner:** ContosoRetail (Trading Partner)
- **Transaction Sets:** 997
- **Used In:** Demos 3 & 4

### Partner Configuration

Create two partners in your Integration Account:

**Partner 1: FabrikamSupplies** (Your Organization)
- Qualifier: ZZ
- Value: FABRIKAMSUPPLY

**Partner 2: ContosoRetail** (Trading Partner)
- Qualifier: ZZ
- Value: CONTOSORETAIL

## Demo 1: Logic App Decoding X12 850 to JSON with All Segments

**File:** [Demo 1/LogicApp_X12_Decode_to_JSON.json](Demo 1/LogicApp_X12_Decode_to_JSON.json)

### Overview
Demonstrates decoding an X12 850 Purchase Order message into JSON format with all segments extracted and organized.

### Key Features
- HTTP trigger accepting raw X12 850 messages
- X12 decode action to parse EDI message
- Comprehensive segment extraction including:
  - ISA (Interchange Control Header)
  - GS (Functional Group Header)
  - ST (Transaction Set Header)
  - BEG (Beginning Segment)
  - REF (Reference Identification)
  - DTM (Date/Time Reference)
  - N1 (Name/Party Identification)
  - PO1 (Purchase Order Baseline Item Data)
  - CTT (Transaction Totals)
  - SE/GE/IEA (Trailer segments)
- Formatted JSON response with summary information

### Use Case
Foundation for any X12 processing workflow - understanding the complete structure of received EDI messages.

---

## Demo 2: Transforming Decoded JSON to Internal Order Format for API

**File:** [Demo 2/LogicApp_X12_to_Internal_Order_Format.json](Demo 2/LogicApp_X12_to_Internal_Order_Format.json)

### Overview
Builds on Demo 1 by transforming decoded X12 JSON into a normalized internal order format suitable for API consumption.

### Key Features
- X12 850 decoding
- Transformation to internal order object with:
  - Order metadata (ID, date, delivery date)
  - Customer and supplier information
  - Line item processing with calculations
  - Total amount computation
- Line item loop processing with:
  - Quantity and unit price extraction
  - Line total calculation
  - Product description mapping
- HTTP POST to internal Order Management API
- Comprehensive metadata tracking (control numbers, timestamps)

### Use Case
Integration bridge between EDI trading partners and internal order management systems.

---

## Demo 3: Generating 997 Acknowledgment for Received X12 Message

**File:** [Demo 3/LogicApp_Generate_997_Acknowledgment.json](Demo 3/LogicApp_Generate_997_Acknowledgment.json)

### Overview
Demonstrates automatic generation of X12 997 Functional Acknowledgment in response to received EDI messages.

### Key Features
- Decodes received X12 850 message
- Extracts control numbers from original message
- Builds compliant 997 acknowledgment XML structure
- Encodes 997 to X12 format using integration account agreement
- Returns both X12 997 message and acknowledgment metadata
- Includes acceptance status (A = Accepted)

### 997 Acknowledgment Structure
- **AK1**: Functional Group Response Header
- **AK2**: Transaction Set Response Header
- **AK5**: Transaction Set Response Trailer (status code)
- **AK9**: Functional Group Response Trailer (statistics)

### Use Case
Critical for B2B EDI compliance - acknowledging receipt and validation of trading partner messages.

---

## Demo 4: Complete B2B Workflow - Receive X12 → Process → Send 997 → Forward JSON

**File:** [Demo 4/LogicApp_Complete_B2B_Workflow.json](Demo 4/LogicApp_Complete_B2B_Workflow.json)

### Overview
End-to-end B2B integration workflow combining all previous demos into a production-ready automated process.

### Complete Workflow Steps

1. **Receive X12 Message**
   - Blob trigger monitors `/incoming-x12` folder
   - Processes files automatically every 3 minutes

2. **Decode & Parse**
   - Decodes X12 850 Purchase Order
   - Extracts control numbers for tracking
   - Parses all transaction data

3. **Transform to Internal Format**
   - Converts to standardized order JSON
   - Adds correlation ID for tracking
   - Includes metadata for auditing

4. **Save Processed Order**
   - Stores JSON order to `/processed-orders` folder
   - Timestamped filename with correlation ID

5. **Generate 997 Acknowledgment**
   - Builds compliant 997 response
   - References original control numbers
   - Encodes to X12 format

6. **Save 997 Acknowledgment**
   - Stores to `/acknowledgments-997` folder
   - Maintains audit trail

7. **Send 997 to Trading Partner**
   - HTTP POST to partner EDI endpoint
   - Includes correlation headers

8. **Forward Order to Internal API**
   - Sends transformed JSON to Order Management API
   - Includes API key authentication

9. **Archive & Cleanup**
   - Creates comprehensive processing summary
   - Moves original X12 to archive
   - Deletes processed file from incoming folder

### Key Features
- **Correlation tracking** with unique IDs throughout workflow
- **Complete audit trail** with processing logs
- **Error handling** with status tracking
- **Blob organization** with dedicated folders:
  - `/incoming-x12` - New X12 messages
  - `/processed-orders` - Transformed JSON orders
  - `/acknowledgments-997` - Generated 997s
  - `/processing-logs` - Workflow summaries
  - `/archive-x12` - Completed original files

### Monitoring & Observability
- Processing summary includes:
  - All workflow steps with status
  - Timestamps and correlation IDs
  - Control numbers and identifiers
  - API response codes
  - Complete order data

### Use Case
Production-ready B2B EDI integration solution for automated order processing with full compliance and traceability.

---

## Prerequisites

All demos require:
- Azure Logic App (Standard or Consumption)
- Integration Account with X12 agreements configured
- X12 connector connection
- Blob Storage connection (Demo 4)

### Integration Account Requirements
- X12 agreements for encoding/decoding
- Trading partner identifiers configured
- 997 acknowledgment agreement (Demos 3 & 4)

---

## Configuration Notes

### Agreement Names
Update these in the workflow definitions to match your Integration Account:
- **Receive agreement**: `ContosoRetail_To_FabrikamSupplies_X12` (for 850 decoding)
- **Send agreement**: `FabrikamSupplies_To_ContosoRetail_X12_997` (for 997 encoding)

### API Endpoints
Demo 2 and Demo 4 include placeholder API endpoints:
- Order API: `https://your-order-api.example.com/api/orders`
- Partner EDI endpoint: `https://partner-edi-endpoint.example.com/acknowledgments`

Update these to match your actual endpoints.

### Blob Storage Folders
Demo 4 uses the following folder structure (create in your storage account):
```
/incoming-x12           # Drop X12 files here
/processed-orders       # Transformed JSON output
/acknowledgments-997    # Generated 997s
/processing-logs        # Workflow summaries
/archive-x12           # Archived originals
```

---

## Testing

### Demo 1 & 2 Testing
Send POST request with X12 message:
```json
{
  "x12Message": "ISA*00*...[your X12 850 message]...IEA*1*000000001~"
}
```

### Demo 3 Testing
Same as Demo 1 & 2 - provide X12 850 message for acknowledgment generation.

### Demo 4 Testing
Upload X12 850 file to `/incoming-x12` blob folder and monitor workflow execution.

---

## Learning Progression

1. **Demo 1**: Understand X12 structure and decoding
2. **Demo 2**: Learn data transformation and API integration
3. **Demo 3**: Implement EDI compliance with 997 acknowledgments
4. **Demo 4**: Build complete production workflow

Each demo builds on concepts from previous demos, culminating in a complete B2B integration solution.
