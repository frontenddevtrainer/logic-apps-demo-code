# Day 2-5: Transform DB Data into API DTOs

Real-world pattern: Azure Function queries database, transforms raw data into clean API DTOs (Data Transfer Objects), and returns structured JSON suitable for client consumption.

## Why Transform Data?

### ❌ Bad Practice: Return Raw DB Data
```python
# Returns internal database structure to clients
cursor.execute("SELECT * FROM orders")
return cursor.fetchall()
# Problems:
# - Exposes internal database structure
# - Contains sensitive data
# - Inconsistent formatting
# - Hard to version API
```

### ✅ Good Practice: Transform to DTOs
```python
# Returns clean, versioned API response
db_row = cursor.fetchone()
order_dto = transform_order_from_db(db_row)
return order_dto.model_dump()
# Benefits:
# - Hide sensitive data
# - Consistent API contract
# - Easy to version
# - Add calculated fields
```

## Features

- ✅ **Data Transformation**: Raw DB → Clean DTOs
- ✅ **Hide Sensitive Data**: Mask payment info, internal IDs
- ✅ **Calculated Fields**: Aggregate data, derived values
- ✅ **Formatted Output**: Proper date formats, parsed addresses
- ✅ **Type Safety**: Pydantic models with validation
- ✅ **API Versioning**: Decouple API from database schema

## Setup

### 1. Install Dependencies
```bash
cd Day2-5-Transform-DB-Data
pip install -r requirements.txt
```

### 2. Configure Database
Edit `local.settings.json` with your PostgreSQL credentials.

### 3. Create Tables
Run `setup.sql` to create tables and sample data.

### 4. Run Locally
```bash
func start
```

## API Endpoints

### 1. Get Customer (with aggregates)
```bash
GET /api/customer/{customer_id}

# Example
curl http://localhost:7071/api/customer/CUST-0001
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "customer_id": "CUST-0001",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "member_since": "2024-01-15T10:30:00",
    "total_orders": 25,
    "total_spent": 5432.50,
    "status": "active"
  }
}
```

### 2. Get Customer Orders (transformed)
```bash
GET /api/customer/{customer_id}/orders

# Example
curl http://localhost:7071/api/customer/CUST-0001/orders
```

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "data": [
    {
      "order_id": 1001,
      "order_number": "ORD-2024-001001",
      "customer_name": "John Doe",
      "customer_email": "john.doe@example.com",
      "order_date": "2024-12-15T10:30:00",
      "status": "COMPLETED",
      "total_amount": 299.99,
      "items_count": 3,
      "shipping_address": {
        "street": "123 Main St",
        "city": "City",
        "state": "State",
        "zip": "12345"
      },
      "payment_info": {
        "method": "Credit Card",
        "last_four": "****"
      }
    }
  ]
}
```

### 3. Get Product Catalog (with stock levels)
```bash
GET /api/products/catalog?category=Electronics&in_stock_only=true

# Example
curl "http://localhost:7071/api/products/catalog?category=Electronics"
```

**Response:**
```json
{
  "status": "success",
  "total_count": 6,
  "in_stock_count": 5,
  "out_of_stock_count": 1,
  "data": {
    "in_stock": [
      {
        "product_id": 1,
        "sku": "SKU-000001",
        "name": "Laptop Pro 15",
        "category": "Electronics",
        "price": 1299.99,
        "discount_price": null,
        "in_stock": true,
        "stock_level": "medium",
        "image_url": null
      }
    ],
    "out_of_stock": []
  }
}
```

### 4. Get Order Details (complete)
```bash
GET /api/order/{order_id}

# Example
curl http://localhost:7071/api/order/1001
```

## Transformation Examples

### Customer Transformation
```python
# Raw DB Row:
{
  "customer_id": "CUST-0001",
  "full_name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-123-4567",
  "created_at": datetime(2024, 1, 15, 10, 30),
  "is_active": True,
  "order_count": 25,
  "total_spent": Decimal("5432.50")
}

# Transformed DTO:
{
  "customer_id": "CUST-0001",
  "name": "John Doe",  # Renamed field
  "email": "john.doe@example.com",
  "phone": "+1-555-123-4567",
  "member_since": "2024-01-15T10:30:00",  # Formatted date
  "total_orders": 25,  # Renamed field
  "total_spent": 5432.50,  # Decimal → float
  "status": "active"  # Calculated from is_active
}
```

### Product Transformation
```python
# Raw DB Row:
{
  "product_id": 1,
  "product_name": "Laptop Pro 15",
  "category": "Electronics",
  "price": Decimal("1299.99"),
  "stock_quantity": 25
}

# Transformed DTO:
{
  "product_id": 1,
  "sku": "SKU-000001",  # Generated
  "name": "Laptop Pro 15",
  "category": "Electronics",
  "price": 1299.99,
  "discount_price": null,  # Could calculate from promotions
  "in_stock": true,  # Calculated from stock_quantity
  "stock_level": "medium",  # Categorized: high/medium/low/out_of_stock
  "image_url": null  # Could generate from product_id
}
```

## Integration with Logic App

Logic Apps can call these functions to get clean, transformed data:

```json
{
  "actions": {
    "Get_Customer_Orders": {
      "type": "Http",
      "inputs": {
        "method": "GET",
        "uri": "https://my-function.azurewebsites.net/api/customer/@{triggerBody()['customerId']}/orders"
      }
    },
    "Response": {
      "type": "Response",
      "inputs": {
        "statusCode": 200,
        "body": "@body('Get_Customer_Orders')?['data']"
      }
    }
  }
}
```

## Testing

Run the test script:
```bash
python test_function.py
```

## Best Practices

1. **Separate Concerns**
   - Database access in function
   - Transformation logic in models.py
   - API contract defined by DTOs

2. **Hide Sensitive Data**
   - Never expose raw passwords
   - Mask payment information
   - Hide internal database IDs when possible

3. **Calculate Derived Fields**
   - Total orders, total spent
   - Stock levels (high/medium/low)
   - Human-readable identifiers

4. **Format for Clients**
   - Parse complex strings (addresses)
   - Format dates consistently
   - Convert Decimal to float for JSON

5. **Version Your API**
   - DTOs decouple API from database
   - Can change database without breaking clients
   - Easy to add new fields
