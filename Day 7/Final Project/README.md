# Final Project: X12 850 Order Processing System

A complete order processing system that combines HTTP triggers, Azure Functions, PostgreSQL, and Blob Storage to process X12 850 Purchase Orders.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────────────────────┐
│   HTTP Client   │────▶│   Logic App      │────▶│   Azure Function                    │
│   (X12 850 PO)  │     │   (HTTP Trigger) │     │   (process-order)                   │
└─────────────────┘     └──────────────────┘     │                                     │
                                                  │  1. Parse X12 message               │
                                                  │  2. Load mapping from Blob Storage  │
                                                  │  3. Transform X12 → JSON            │
                                                  │  4. Validate order data             │
                                                  │  5. Store in PostgreSQL             │
                                                  │  6. Save document to Blob Storage   │
                                                  │  7. Return confirmation              │
                                                  └─────────────────────────────────────┘
                                                           │           │
                                                           ▼           ▼
                                                  ┌─────────────┐ ┌─────────────┐
                                                  │ PostgreSQL  │ │    Blob     │
                                                  │  Database   │ │   Storage   │
                                                  │  (orders)   │ │ (documents) │
                                                  └─────────────┘ └─────────────┘
```

## Components

### 1. Azure Function (`order-processing-function/`)

Two HTTP endpoints:

| Endpoint | Description |
|----------|-------------|
| `POST /api/x12-map` | Parse and map X12 to JSON (no storage) |
| `POST /api/process-order` | Full order processing with validation and storage |

### 2. Logic App (`LogicApp_Order_Processing.json`)

- HTTP-triggered workflow
- Receives X12 850 messages
- Calls Azure Function for processing
- Returns success/error response

### 3. PostgreSQL Database (`database/schema.sql`)

Tables:
- `orders` - Main order records
- `order_items` - Line item details
- `order_status_history` - Status change tracking

### 4. Blob Storage

- **x12-mappings** container: X12 to JSON mapping files
- **order-documents** container: Processed order documents

### 5. X12 850 Mapping (`mappings/standards/850.json`)

Configurable mapping rules for transforming X12 850 Purchase Orders to JSON.

## Project Structure

```
Final Project/
├── README.md                          # This file
├── curl-examples.md                   # Test examples with X12 messages
├── LogicApp_Order_Processing.json     # Logic App ARM template
├── database/
│   └── schema.sql                     # PostgreSQL schema
├── mappings/
│   └── standards/
│       └── 850.json                   # X12 850 mapping configuration
└── order-processing-function/
    ├── function_app.py                # Azure Function code
    ├── host.json                      # Function host configuration
    ├── local.settings.json            # Local environment settings
    ├── requirements.txt               # Python dependencies
    └── mapping_logic/
        ├── __init__.py
        └── mapper.py                  # X12 mapping engine
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Azure Functions Core Tools
- Azure CLI
- PostgreSQL (Azure Database for PostgreSQL or local)
- Azure Storage Account

### 1. Create Azure Resources

```bash
# Activate Azurite 
set AZURITE_ACCOUNTS="account1:key1:key2"

# on windows use set
export AZURITE_CONNECTION_STRING='DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFeqCnf2L+ZzqQ7yF0+XkX7m7Z5eKxF5AqzJv9xq0x6VJ+VjN5E4xV4l0v9oJ0+QJw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;'

# Create resource group
az group create --name rg-order-processing --location eastus

# Create storage account
az storage account create \
  --name orderprocessingstorage \
  --resource-group rg-order-processing \
  --location eastus \
  --sku Standard_LRS



# Copy Files to container

az storage blob upload \
  --container-name mycontainer \
  --name mappings/standards/850.json \
  --file mappings/standards/850.json \
  --connection-string "$AZURITE_CONNECTION_STRING" \
  --overwrite true

# Create blob containers
az storage container create --name x12-mappings --account-name orderprocessingstorage
az storage container create --name order-documents --account-name orderprocessingstorage

# Create PostgreSQL server
az postgres flexible-server create \
  --name order-processing-db \
  --resource-group rg-order-processing \
  --location eastus \
  --admin-user adminuser \
  --admin-password <your-password> \
  --sku-name Standard_B1ms \
  --tier Burstable
```

### 2. Setup PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -h order-processing-db.postgres.database.azure.com -U adminuser -d postgres

# Create database
CREATE DATABASE order_processing;

# Connect to the new database
\c order_processing

# Run schema script
\i database/schema.sql
```

### 3. Upload Mapping Files

```bash
# Upload 850 mapping to Blob Storage
az storage blob upload \
  --account-name orderprocessingstorage \
  --container-name x12-mappings \
  --name mapping/standards/850.json \
  --file mappings/standards/850.json
```

### 4. Configure Local Settings

Edit `order-processing-function/local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "<storage-connection-string>",
    "MAPPING_STORAGE_CONNECTION": "<storage-connection-string>",
    "MAPPING_CONTAINER": "x12-mappings",
    "MAPPING_ROOT": "mapping",
    "ORDER_STORAGE_CONNECTION": "<storage-connection-string>",
    "ORDER_CONTAINER": "order-documents",
    "POSTGRES_HOST": "<server>.postgres.database.azure.com",
    "POSTGRES_DB": "order_processing",
    "POSTGRES_USER": "<username>",
    "POSTGRES_PASSWORD": "<password>",
    "POSTGRES_PORT": "5432",
    "POSTGRES_SSLMODE": "require"
  }
}
```

### 5. Run Locally

```bash
cd "order-processing-function"

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Start function
func start
```

### 6. Deploy Azure Function

```bash
# Create Function App
az functionapp create \
  --name order-processing-func \
  --resource-group rg-order-processing \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.9 \
  --storage-account orderprocessingstorage \
  --functions-version 4

# Deploy code
func azure functionapp publish order-processing-func

# Configure app settings
az functionapp config appsettings set \
  --name order-processing-func \
  --resource-group rg-order-processing \
  --settings \
    POSTGRES_HOST=<server>.postgres.database.azure.com \
    POSTGRES_DB=order_processing \
    POSTGRES_USER=<username> \
    POSTGRES_PASSWORD=<password> \
    MAPPING_CONTAINER=x12-mappings \
    ORDER_CONTAINER=order-documents
```

### 7. Deploy Logic App

```bash
az deployment group create \
  --resource-group rg-order-processing \
  --template-file LogicApp_Order_Processing.json \
  --parameters \
    functionAppUrl=https://order-processing-func.azurewebsites.net/api/process-order
```

## Usage

### Send X12 850 Order

```bash
curl -X POST "http://localhost:7071/api/process-order" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*PO-2024-001**20240115~N1*BY*Acme Corp*92*ACME-001~PO1*001*10*EA*29.99*PE*VP*PROD-001~CTT*1*10~SE*6*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }'
```

### Response

```json
{
  "success": true,
  "message": "Order processed successfully",
  "orderId": "ORD-20240115-A1B2C3D4",
  "orderDate": "2024-01-15T10:30:00.000Z",
  "status": "pending",
  "summary": {
    "purchaseOrderNumber": "PO-2024-001",
    "buyer": "Acme Corp",
    "itemCount": 1,
    "totalAmount": 299.90
  },
  "storage": {
    "database": "Order saved to PostgreSQL",
    "blobPath": "order-documents/2024/01/15/ORD-20240115-A1B2C3D4.json"
  },
  "warnings": []
}
```

## X12 850 Segment Mapping

| X12 Segment | JSON Field | Description |
|-------------|------------|-------------|
| BEG-03 | purchaseOrderNumber | PO Number |
| BEG-05 | purchaseOrderDate | PO Date |
| N1 (BY) | buyer.* | Buyer information |
| N1 (ST) | shipTo.* | Ship-to address |
| N1 (SE) | seller.* | Seller information |
| PO1 | items[] | Line items |
| PID | items[].description | Product description |
| CTT | summary.totalLineItems | Total line count |
| AMT (TT) | summary.totalAmount | Total amount |

## API Reference

### POST /api/process-order

Process X12 850 Purchase Order with full validation and storage.

**Request Body:**
```json
{
  "x12": "ISA*00*...",           // Raw X12 message (required)
  "transactionSet": "850",       // Transaction type (default: 850)
  "client": "acme",              // Client ID for mapping selection
  "mappingPath": "path/to.json"  // Override mapping path
}
```

**Response (Success - 201):**
```json
{
  "success": true,
  "orderId": "ORD-XXXXXXXX",
  "summary": { ... },
  "storage": { ... }
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "errors": ["..."],
  "warnings": ["..."]
}
```

### POST /api/x12-map

Map X12 to JSON without storage (from Demo 5).

**Request Body:**
```json
{
  "x12": "ISA*00*...",
  "transactionSet": "850",
  "includeMeta": true
}
```

## Course Integration

This project combines concepts from:

- **HTTP Triggers**: Logic App receives X12 orders via HTTP POST
- **Azure Functions**: Python function for X12 parsing, mapping, validation
- **PostgreSQL**: Order and line item storage with relational integrity
- **Blob Storage**: X12 mapping files and processed order documents

## Troubleshooting

### Common Issues

1. **Mapping not found**: Upload 850.json to `x12-mappings/mapping/standards/`
2. **PostgreSQL connection failed**: Check firewall rules and SSL mode
3. **Blob upload failed**: Verify storage connection string and container exists

### Logs

```bash
# View function logs
func azure functionapp logstream order-processing-func

# View Logic App runs
az monitor log-analytics query --workspace <workspace-id> --analytics-query "AzureDiagnostics | where Category == 'WorkflowRuntime'"
```

## License

MIT License - Educational use for Azure Logic Apps training course.
