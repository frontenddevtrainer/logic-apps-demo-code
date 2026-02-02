# Day 2-3: Filter/Select Query with Pagination

Azure Function demonstrating best practices for filtering database queries with pagination instead of retrieving entire tables.

## Key Concepts
- ✅ **Filter at database level** using WHERE clauses
- ✅ **Pagination** with LIMIT/OFFSET
- ✅ **Projection** - select only needed columns
- ✅ Calculate total pages and count
- ✅ Return pagination metadata

## Setup

### 1. Install Dependencies
```bash
cd Day2-3-Filtered-Queries
pip install -r requirements.txt
```

### 2. Configure Local Settings
Edit `local.settings.json` with your PostgreSQL credentials.

### 3. Create Database Table
Run `setup.sql` to create the orders table and sample data.

### 4. Run Locally
```bash
func start
```

## API Usage

### Endpoint
```
GET/POST http://localhost:7071/api/orders
```

### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| status | string | Yes | - | Order status: PENDING, PROCESSING, COMPLETED, CANCELLED |
| startDate | string | No | 30 days ago | Start date (YYYY-MM-DD) |
| endDate | string | No | Today | End date (YYYY-MM-DD) |
| page | integer | No | 1 | Page number (1-based) |
| pageSize | integer | No | 100 | Records per page (max: 500) |

### Request Examples

#### Page 1 - First 100 completed orders
```bash
curl -X POST http://localhost:7071/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "status": "COMPLETED",
    "page": 1,
    "pageSize": 100
  }'
```

#### Page 2 - Next 100 orders
```bash
curl -X POST http://localhost:7071/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "status": "COMPLETED",
    "page": 2,
    "pageSize": 100
  }'
```

#### Custom date range
```bash
curl -X POST http://localhost:7071/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "status": "PENDING",
    "startDate": "2024-01-01",
    "endDate": "2024-12-31",
    "page": 1,
    "pageSize": 50
  }'
```

### Response Example
```json
{
  "status": "success",
  "pagination": {
    "page": 1,
    "pageSize": 100,
    "totalRecords": 523,
    "totalPages": 6,
    "hasNextPage": true,
    "hasPreviousPage": false
  },
  "filters": {
    "status": "COMPLETED",
    "startDate": "2024-01-01",
    "endDate": "2024-12-31"
  },
  "data": [
    {
      "order_id": 1001,
      "customer_id": "CUST-001",
      "order_date": "2024-12-15T10:30:00",
      "total_amount": 299.99,
      "status": "COMPLETED",
      "shipping_address": "123 Main St, City, State 12345",
      "payment_method": "Credit Card"
    }
  ]
}
```

## Performance Best Practices

### ✅ DO THIS
```python
# Filter at database level with pagination
query = """
    SELECT order_id, customer_id, order_date, total_amount
    FROM orders
    WHERE status = %s AND order_date >= %s
    ORDER BY order_date DESC
    LIMIT %s OFFSET %s
"""
cursor.execute(query, (status, start_date, page_size, offset))
```

### ❌ DON'T DO THIS
```python
# BAD: Fetch all data and filter in Python
query = "SELECT * FROM orders"
cursor.execute(query)
all_orders = cursor.fetchall()
filtered = [o for o in all_orders if o['status'] == status]
```

## Pagination Calculation

```python
# Page 1: offset = (1 - 1) * 100 = 0    → Records 1-100
# Page 2: offset = (2 - 1) * 100 = 100  → Records 101-200
# Page 3: offset = (3 - 1) * 100 = 200  → Records 201-300

offset = (page - 1) * page_size
total_pages = math.ceil(total_count / page_size)
```

## Testing

Run the test script:
```bash
python test_function.py
```

## Deploy to Azure

```bash
# Create Function App
az functionapp create \
  --resource-group myResourceGroup \
  --consumption-plan-type EP1 \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name myOrdersFunction \
  --storage-account mystorageaccount

# Deploy
func azure functionapp publish myOrdersFunction
```
