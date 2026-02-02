# Day 2-2: Execute SQL Query with Dynamic Content Binding

Azure Function that demonstrates parameterized SQL queries to prevent SQL injection and handle dynamic filtering.

## Features
- ✅ Parameterized SQL queries (prevents SQL injection)
- ✅ Dynamic content binding from HTTP request
- ✅ Input validation
- ✅ Error handling
- ✅ PostgreSQL connection with SSL

## Setup

### 1. Install Dependencies
```bash
cd Day2-2-Dynamic-SQL-Query
pip install -r requirements.txt
```

### 2. Configure Local Settings
Edit `local.settings.json` with your PostgreSQL credentials:
```json
{
  "Values": {
    "POSTGRES_HOST": "your-server.postgres.database.azure.com",
    "POSTGRES_DATABASE": "your-database",
    "POSTGRES_USER": "your-username",
    "POSTGRES_PASSWORD": "your-password"
  }
}
```

### 3. Create Database Table
Run the SQL from `setup.sql` to create the products table and sample data.

### 4. Run Locally
```bash
func start
```

## API Usage

### Endpoint
```
GET/POST http://localhost:7071/api/products
```

### Request Examples

#### GET Request
```bash
curl "http://localhost:7071/api/products?category=Electronics&maxPrice=500&minStock=10"
```

#### POST Request
```bash
curl -X POST http://localhost:7071/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Electronics",
    "maxPrice": 500,
    "minStock": 10
  }'
```

### Response Example
```json
{
  "status": "success",
  "count": 2,
  "filters": {
    "category": "Electronics",
    "maxPrice": 500,
    "minStock": 10
  },
  "data": [
    {
      "product_id": 1,
      "product_name": "Laptop Pro 15",
      "category": "Electronics",
      "price": 299.99,
      "stock_quantity": 25,
      "description": "High-performance laptop",
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

## Security Best Practices

### ✅ DO THIS - Parameterized Queries
```python
# Safe - uses parameterized query
query = "SELECT * FROM products WHERE category = %s AND price <= %s"
cursor.execute(query, (category, max_price))
```

### ❌ DON'T DO THIS - String Concatenation
```python
# UNSAFE - SQL injection vulnerability!
query = f"SELECT * FROM products WHERE category = '{category}'"
cursor.execute(query)
```

## Deploy to Azure

### 1. Create Function App
```bash
az functionapp create \
  --resource-group myResourceGroup \
  --consumption-plan-type EP1 \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name myProductsFunction \
  --storage-account mystorageaccount
```

### 2. Configure App Settings
```bash
az functionapp config appsettings set \
  --name myProductsFunction \
  --resource-group myResourceGroup \
  --settings \
    POSTGRES_HOST="your-server.postgres.database.azure.com" \
    POSTGRES_DATABASE="your-database" \
    POSTGRES_USER="your-username" \
    POSTGRES_PASSWORD="@Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/postgres-password/)"
```

### 3. Deploy Function
```bash
func azure functionapp publish myProductsFunction
```

## Testing

Run the test script:
```bash
python test_function.py
```
