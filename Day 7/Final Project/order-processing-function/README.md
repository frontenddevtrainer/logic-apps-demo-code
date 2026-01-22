# Order Processing Azure Function

Azure Function for processing X12 850 Purchase Orders. Parses X12 EDI messages, maps them to JSON, validates orders, and stores them in Blob Storage and PostgreSQL.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local) v4+
- Node.js (for Azurite)
- PostgreSQL (optional, for database storage)

## Quick Start

Run the development environment with a single command:

```bash
./scripts/start_dev.sh
```

This will:
1. Start Azurite (if not already running)
2. Create required blob containers
3. Upload the X12 850 mapping file
4. Start the Azure Function

## Manual Development Setup

### 1. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Azurite (Azure Storage Emulator)

```bash
npx azurite --location ./azurite --blobHost 127.0.0.1 --queueHost 127.0.0.1 --tableHost 127.0.0.1 --skipApiVersionCheck
```

This starts:
- Blob service: http://127.0.0.1:10000
- Queue service: http://127.0.0.1:10001
- Table service: http://127.0.0.1:10002

### 4. Create required blob containers and upload mapping

```bash
source venv/bin/activate
python3 scripts/setup_azurite.py
```

Or manually with Python:

```python
from azure.storage.blob import BlobServiceClient

conn_str = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"

service = BlobServiceClient.from_connection_string(conn_str)
service.create_container("x12-mappings")
service.create_container("order-documents")
```

### 5. Configure local settings

The `local.settings.json` should already be configured for Azurite. Verify it contains:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;",
    "MAPPING_STORAGE_CONNECTION": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;",
    "MAPPING_CONTAINER": "x12-mappings",
    "MAPPING_ROOT": "mapping",
    "ORDER_STORAGE_CONNECTION": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;",
    "ORDER_CONTAINER": "order-documents"
  }
}
```

### 6. Start the Azure Function

```bash
source venv/bin/activate
func start
```

The function will be available at:
- http://localhost:7071/api/x12-map
- http://localhost:7071/api/process-order

## API Endpoints

### POST /api/x12-map

Maps X12 EDI message to JSON.

**Request:**
```json
{
  "x12": "ISA*00*...",
  "transactionSet": "850"
}
```

**Response:**
```json
{
  "purchaseOrderNumber": "PO12345",
  "purchaseOrderDate": "20230101",
  "buyer": { "id": "BUYER123", "name": "Acme Corp" },
  "items[]": { "productId": "PROD001", "quantity": "10" }
}
```

### POST /api/process-order

Full order processing: parse, map, validate, and store.

**Request:**
```json
{
  "x12": "ISA*00*...",
  "transactionSet": "850"
}
```

**Response:**
```json
{
  "success": true,
  "orderId": "ORD-20260122-ABCD1234",
  "message": "Order processed successfully",
  "storage": {
    "blobPath": "order-documents/2026/01/22/ORD-20260122-ABCD1234.json"
  }
}
```

## Testing with cURL

### Test x12-map endpoint

```bash
curl -X POST http://localhost:7071/api/x12-map \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*850*0001~BEG*00*NE*PO12345**20230101~N1*BY*Acme Corp*92*BUYER123~N1*SE*Supplier Inc*92*SELL456~PO1*1*10*EA*25.00*PE*VP*PROD001*UP*123456789~PID*F****Widget A~CTT*1~SE*9*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }'
```

### Test process-order endpoint

```bash
curl -X POST http://localhost:7071/api/process-order \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20230101*1200*1*X*004010~ST*850*0001~BEG*00*NE*PO12345**20230101~N1*BY*Acme Corp*92*BUYER123~N1*SE*Supplier Inc*92*SELL456~PO1*1*10*EA*25.00*PE*VP*PROD001*UP*123456789~PID*F****Widget A~CTT*1~SE*9*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }'
```

### Sample X12 850 Message

```
ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *230101*1200*U*00401*000000001*0*P*:~
GS*PO*SENDER*RECEIVER*20230101*1200*1*X*004010~
ST*850*0001~
BEG*00*NE*PO12345**20230101~
N1*BY*Acme Corp*92*BUYER123~
N1*SE*Supplier Inc*92*SELL456~
PO1*1*10*EA*25.00*PE*VP*PROD001*UP*123456789~
PID*F****Widget A~
CTT*1~
SE*9*0001~
GE*1*1~
IEA*1*000000001~
```

## Project Structure

```
order-processing-function/
├── function_app.py          # Main Azure Function code
├── mapping_logic/
│   ├── __init__.py
│   └── mapper.py            # X12 to JSON mapping logic
├── requirements.txt         # Python dependencies
├── local.settings.json      # Local configuration
├── host.json                # Azure Functions host config
├── scripts/
│   ├── start_dev.sh         # Start development environment
│   └── setup_azurite.py     # Setup Azurite containers
├── azurite/                 # Azurite data (gitignored)
└── venv/                    # Virtual environment (gitignored)
```

## PostgreSQL Setup (Optional)

To enable database storage, configure PostgreSQL settings in `local.settings.json`:

```json
{
  "Values": {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_DB": "order_processing",
    "POSTGRES_USER": "your_user",
    "POSTGRES_PASSWORD": "your_password",
    "POSTGRES_PORT": "5432",
    "POSTGRES_SSLMODE": "disable"
  }
}
```



cd "/Users/trainer/logic-apps-demo/Day 7/Final Project/order-processing-function" && source venv/bin/activate && python3 << 'EOF'
from azure.storage.blob import BlobServiceClient

conn_str = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"

service = BlobServiceClient.from_connection_string(conn_str)

print("=== Blob Container Contents ===\n")
for container in service.list_containers():
    print(f"Container: {container.name}")
    print("-" * 40)
    container_client = service.get_container_client(container.name)
    blobs = list(container_client.list_blobs())
    if not blobs:
        print("  (empty)")
    for blob in blobs:
        print(f"  - {blob.name} ({blob.size} bytes)")
    print()
EOF