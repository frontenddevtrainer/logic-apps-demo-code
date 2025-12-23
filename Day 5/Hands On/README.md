# Hands On: End-to-End CSV to X12 Transformation with Blob Storage

## Overview
This hands-on exercise implements a complete enterprise integration workflow that:
1. **Receives CSV file** via blob storage upload (incoming-orders container)
2. **Parses CSV** and validates required fields using flat file schema
3. **Transforms to X12 850** Purchase Order using Integration Account map
4. **Validates against X12 schema** to ensure data quality
5. **Stores valid X12 file** in blob storage (x12-output container)
6. **Archives or moves files** based on processing outcome

This combines concepts from Demo 3 (CSV to X12 transformation) and Demo 4 (XML validation and error handling) with cloud-native blob storage triggers.

## Architecture Flow

```
[Upload CSV] → [Blob Trigger] → [Get Content] → [Decode CSV] → [Transform] → [Validate]
                                                                                   ↓
                                                                             [Condition]
                                                                                   ↓
                                                  ┌────────────────────────────────┴──────────┐
                                                  ↓                                           ↓
                                            [Valid Path]                              [Invalid Path]
                                                  ↓                                           ↓
                                          [Encode X12]                              [Create Error]
                                                  ↓                                           ↓
                                        [Save X12 Blob]                             [Move to /errors]
                                                  ↓
                                        [Move to /archive]
```

## Blob Storage Containers

You'll create 5 containers in your storage account:

| Container | Purpose |
|-----------|---------|
| `incoming-orders` | Upload CSV files here (monitored by trigger) |
| `x12-output` | Successfully generated X12 files |
| `archive` | Successfully processed CSV files |
| `errors` | CSV files that failed validation |
| `validation-errors` | Detailed error information (JSON) |

## Prerequisites

### Azure Resources
- ✅ Integration Account with schemas, maps, and agreements (from Demo 1)
- ✅ Azure Storage Account
- ✅ Logic App (Consumption tier)

### Integration Account Assets
- ✅ Schema: `orders-flatfile` (CSV schema)
- ✅ Schema: `X12_00401_850` (X12 validation schema)
- ✅ Map: `CsvToX12_850` (XSLT transformation)
- ✅ Agreement: `ContosoRetail_To_FabrikamSupplies_X12`

## Quick Start (5 Steps)

### Step 1: Create Blob Containers

```
Storage Account → Containers → + Container

Create these 5 containers:
1. incoming-orders
2. x12-output
3. archive
4. errors
5. validation-errors
```

### Step 2: Create Blob Connection

```
Azure Portal → API Connections → + Add → Azure Blob Storage

Name: azureblob
Storage Account: [select yours]
Authentication: Access Key or Managed Identity
```

### Step 3: Create Logic App

```
Azure Portal → Logic Apps → + Add

Name: CSV-to-X12-Blob-Processor
Region: UK South
Plan: Consumption

After creation:
Settings → Workflow settings → Integration account → [Select yours]
```

### Step 4: Import Workflow

```
Logic App → Logic app designer → Code view

Copy/paste: LogicApp_CSV_to_X12_Blob_Trigger.json

Save
```

### Step 5: Test

```
Upload sample-data/orders.csv to incoming-orders container

Wait 1-2 minutes

Check:
- x12-output: Should contain .x12 file
- archive: Should contain orders.csv
- incoming-orders: Should be empty
```

## Testing

### Upload Test File (Azure Portal)

```
Storage Account → Containers → incoming-orders → Upload
Select file: sample-data/orders.csv
Click Upload
```

### Upload Test File (Azure CLI)

```bash
az storage blob upload \
  --account-name YOUR_STORAGE_ACCOUNT \
  --container-name incoming-orders \
  --name orders.csv \
  --file sample-data/orders.csv
```

### Upload Test File (PowerShell)

```powershell
$ctx = New-AzStorageContext -StorageAccountName "YOUR_STORAGE_ACCOUNT" -UseConnectedAccount
Set-AzStorageBlobContent `
  -File "sample-data/orders.csv" `
  -Container "incoming-orders" `
  -Blob "orders.csv" `
  -Context $ctx
```

## Expected Results

### Test 1: orders.csv (Valid) ✅

| Step | Result |
|------|--------|
| Trigger | Logic App runs |
| Decode | CSV → XML |
| Transform | CSV XML → X12 XML |
| Validate | ✅ Pass |
| Encode | X12 EDI generated |
| Output | `x12-output/PO2025001_*.x12` created |
| Archive | `archive/orders.csv` created |
| Cleanup | `incoming-orders` empty |

### Test 2: orders-invalid.csv (Invalid) ❌

| Step | Result |
|------|--------|
| Trigger | Logic App runs |
| Decode | CSV → XML |
| Transform | CSV XML → X12 XML (incomplete) |
| Validate | ❌ Fail (missing OrderNumber) |
| Error | `validation-errors/ERROR_*.json` created |
| Move | `errors/orders-invalid.csv` created |
| No X12 | `x12-output` unchanged |

## Workflow Actions

The Logic App contains these actions:

1. **When a blob is added or modified** (Trigger)
   - Container: incoming-orders
   - Polling: Every 1 minute

2. **Initialize_CorrelationId** - Tracking GUID

3. **Initialize_FileName** - File name variable

4. **Get_blob_content** - Retrieves CSV content

5. **Flat_File_Decoding** - CSV → XML

6. **Transform_XML** - CSV XML → X12 XML

7. **Validate_XML** - Check against schema

8. **Condition** - Route based on validation

   **True (Valid):**
   - Encode_to_X12_message
   - Extract_OrderNumber
   - Create_X12_Blob (to x12-output)
   - Move_to_Archive (to archive)

   **False (Invalid):**
   - Create_Error_Blob (to validation-errors)
   - Move_to_Errors_Folder (to errors)

## Troubleshooting

### Logic App doesn't trigger
- Check container name: `incoming-orders` (exact match)
- Wait 1-2 minutes (polling interval)
- Verify blob connection status: Connected
- Check file uploaded successfully

### "Schema not found" error
- Verify Integration Account linked
- Check schema names (case-sensitive):
  - `orders-flatfile`
  - `X12_00401_850`
- Re-upload schemas if needed

### Blob operations fail
- Check blob connection authorized
- Verify containers exist
- Ensure storage account accessible
- Check permissions (Storage Blob Data Contributor)

## Cost Estimate

Monthly cost for 1,000 files:

| Item | Cost |
|------|------|
| Logic App (6 actions × 1000) | $0.60 |
| Blob operations (3000) | $0.30 |
| Storage (100 MB) | $0.02 |
| **Total** | **$0.92** |

## Sample Files

- `orders.csv` - Valid (2 line items)
- `orders-invalid.csv` - Invalid (missing OrderNumber)
- `orders-multi-line.csv` - Valid (4 line items)
- `LogicApp_CSV_to_X12_Blob_Trigger.json` - Workflow definition

## Advanced Topics

### Batch Processing

Process multiple files per execution:
```json
"maxFileCount": 10  // in trigger queries
```

### Event Grid Integration

Trigger downstream systems:
```
Storage Account → Events → + Event Subscription
Event type: Blob Created (x12-output)
Endpoint: Logic App, Function, etc.
```

### Lifecycle Management

Auto-archive old files:
```
Storage Account → Lifecycle management
- Move to Cool after 30 days
- Move to Archive after 90 days
- Delete after 7 years
```

## Resources

- [Azure Blob Storage Connector](https://learn.microsoft.com/connectors/azureblob/)
- [Flat File Processing](https://learn.microsoft.com/azure/logic-apps/logic-apps-enterprise-integration-flatfile)
- [X12 Encoding](https://learn.microsoft.com/azure/logic-apps/logic-apps-enterprise-integration-x12-encode)
- Demo 3: CSV to X12 via HTTP
- Demo 4: XML Validation

---

**Status**: Production Ready
**Complexity**: Simpler than SFTP, cloud-native
**Cost**: ~$0.92/month per 1000 files
