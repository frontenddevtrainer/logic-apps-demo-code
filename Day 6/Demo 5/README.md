# Demo 5: X12 850 Decode and Insert to PostgreSQL Database

## Overview
This demo extends Demo 1 by decoding X12 850 Purchase Order messages and inserting the structured data into a PostgreSQL database. It demonstrates complete data persistence with proper relational database design including header, party, and line item tables.

## Files in This Demo

### Logic App Workflow
- **[LogicApp_X12_Decode_to_PostgreSQL.json](LogicApp_X12_Decode_to_PostgreSQL.json)** - Main workflow definition

### Database Schema
- **[database_schema.sql](database_schema.sql)** - Complete PostgreSQL schema with tables, indexes, and views

## Architecture

### Database Design

The solution uses a normalized relational database design:

```
x12_purchase_orders (Header)
    ├── x12_parties (N1 Loop - Buyer, Ship-To, etc.)
    └── x12_line_items (PO1 Loop - Products)
```

### Tables

#### 1. `x12_purchase_orders` (Header Table)
Stores purchase order header information:
- Purchase order number, dates, control numbers
- Sender/receiver identification
- Order totals and status
- Raw X12 message and decoded JSON (for reference)

#### 2. `x12_parties` (Party Information)
Stores party details from N1 segments:
- Entity type (BY=Buyer, ST=Ship-To, SU=Supplier)
- Party name and identification codes
- Complete address information

#### 3. `x12_line_items` (Line Items)
Stores product line items from PO1 segments:
- Quantity, unit price, line total
- Product IDs and descriptions
- Unit of measure

### Database Views

Two convenient views for querying:
- `vw_purchase_orders_complete` - Complete order info with buyer and ship-to details
- `vw_line_items_summary` - All line items with related order information

## Required Setup

### 1. PostgreSQL Database Setup

#### Option A: Azure Database for PostgreSQL

1. **Create Azure Database for PostgreSQL**
   ```bash
   # Using Azure CLI
   az postgres server create \
     --resource-group your-resource-group \
     --name your-postgres-server \
     --location uksouth \
     --admin-user pgadmin \
     --admin-password YourPassword123! \
     --sku-name B_Gen5_1
   ```

2. **Configure Firewall Rules**
   ```bash
   # Allow Azure services
   az postgres server firewall-rule create \
     --resource-group your-resource-group \
     --server your-postgres-server \
     --name AllowAzureServices \
     --start-ip-address 0.0.0.0 \
     --end-ip-address 0.0.0.0
   ```

3. **Create Database**
   ```bash
   az postgres db create \
     --resource-group your-resource-group \
     --server-name your-postgres-server \
     --name x12_orders_db
   ```

#### Option B: Local PostgreSQL

1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE x12_orders_db;
   ```

### 2. Initialize Database Schema

Connect to your PostgreSQL database and run the schema file:

```bash
# Using psql command line
psql -h your-postgres-server.postgres.database.azure.com \
     -U pgadmin@your-postgres-server \
     -d x12_orders_db \
     -f database_schema.sql

# Or for local PostgreSQL
psql -U postgres -d x12_orders_db -f database_schema.sql
```

This will create:
- 3 tables: `x12_purchase_orders`, `x12_parties`, `x12_line_items`
- Indexes for performance
- Views for easy querying

### 3. Integration Account Setup

Same as Demo 1:

#### Upload Schema
1. Navigate to **Integration Account** > **Schemas**
2. Upload: `../Schemas/X12_00401_850.xsd`
3. Name: `X12_00401_850`

#### Create X12 Agreement
1. Navigate to **Integration Account** > **Agreements**
2. Create agreement: `ContosoRetail_To_FabrikamSupplies_X12`
   - **Agreement Type**: X12
   - **Host Partner**: FabrikamSupplies
   - **Guest Partner**: ContosoRetail
   - **Host Qualifier**: ZZ, **Host Value**: FABRIKAMSUPPLY
   - **Guest Qualifier**: ZZ, **Guest Value**: CONTOSORETAIL

### 4. Logic App Connections

#### X12 Connection
1. Create X12 connector connection
2. Link to Integration Account
3. Update workflow parameters:
   ```json
   "x12": {
     "connectionId": "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/connections/x12",
     "connectionName": "x12"
   }
   ```

#### PostgreSQL Connection
1. In Logic App Designer, add PostgreSQL connector
2. Create connection with your database details:
   - **Server**: your-postgres-server.postgres.database.azure.com
   - **Database**: x12_orders_db
   - **Username**: pgadmin@your-postgres-server
   - **Password**: YourPassword123!
3. Update workflow parameters:
   ```json
   "postgresql": {
     "connectionId": "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/connections/postgresql",
     "connectionName": "postgresql"
   }
   ```

## Testing the Demo

### Test Data Files
Located in `../Sample Data/`:
- **sample_x12_850_purchase_order.x12** - Full X12 850 message with 3 line items
- **sample_x12_850_simple.x12** - Simple X12 850 for basic testing
- **sample_request_demo1.json** - HTTP request body format (reusable)

### How to Test

#### Step 1: Send X12 Message to Logic App

```bash
curl -X POST "https://{your-logic-app-url}" \
  -H "Content-Type: application/json" \
  -d @../Sample\ Data/sample_request_demo1.json
```

Or use the request body:
```json
{
  "x12Message": "ISA*00*          *00*          *ZZ*CONTOSORETAIL  *ZZ*FABRIKAMSUPPLY *231223*1430*U*00401*000000001*0*P*:~GS*PO*CONTOSORETAIL*FABRIKAMSUPPLY*20231223*1430*1*X*004010~ST*850*0001~BEG*00*NE*PO-2023-12345**20231223~..."
}
```

#### Step 2: Verify Data in PostgreSQL

**Query Purchase Orders:**
```sql
-- View all purchase orders
SELECT * FROM vw_purchase_orders_complete;

-- View specific order
SELECT * FROM x12_purchase_orders
WHERE purchase_order_number = 'PO-2023-12345';
```

**Query Parties:**
```sql
-- View all parties for an order
SELECT entity_type, party_name, city, state_province
FROM x12_parties p
JOIN x12_purchase_orders po ON p.purchase_order_id = po.id
WHERE po.purchase_order_number = 'PO-2023-12345';
```

**Query Line Items:**
```sql
-- View line items summary
SELECT * FROM vw_line_items_summary
WHERE purchase_order_number = 'PO-2023-12345';

-- View detailed line items with totals
SELECT
    line_number,
    product_description,
    quantity,
    unit_of_measure,
    unit_price,
    line_total
FROM x12_line_items li
JOIN x12_purchase_orders po ON li.purchase_order_id = po.id
WHERE po.purchase_order_number = 'PO-2023-12345'
ORDER BY line_number;
```

### Expected Response

The Logic App returns:
```json
{
  "status": "success",
  "message": "X12 850 Purchase Order successfully inserted into PostgreSQL",
  "purchaseOrderId": 1,
  "purchaseOrderNumber": "PO-2023-12345",
  "orderDate": "20231223",
  "totalLineItems": "3",
  "timestamp": "2023-12-23T14:30:00Z"
}
```

### Expected Database Records

For `sample_x12_850_purchase_order.x12`:

**1 Purchase Order Header:**
- PO Number: PO-2023-12345
- Order Date: 2023-12-23
- Delivery Date: 2023-12-30
- Total Line Items: 3

**2 Parties:**
- Buyer (BY): Contoso Retail Corporation
- Ship-To (ST): Contoso Warehouse District 5

**3 Line Items:**
1. Premium Alpha Widget - 100 EA × $29.99 = $2,999.00
2. Beta Gadget Pro - 50 EA × $149.99 = $7,499.50
3. Gamma Supply Kit - 200 EA × $5.49 = $1,098.00

**Total Order Value:** $11,596.50

## Workflow Actions Explained

1. **Decode X12 Message** - Parse incoming EDI using Integration Account
2. **Parse X12 Decoded JSON** - Extract structured data
3. **Extract Order Details** - Compose order header information
4. **Get Delivery Date** - Filter DTM segments for delivery date (qualifier '002')
5. **Insert Purchase Order Header** - Insert main order record, get generated ID
6. **Parse Insert Result** - Extract database-generated purchase order ID
7. **For Each Party** - Loop through N1 segments, insert party records
8. **For Each Line Item** - Loop through PO1 segments:
   - Calculate line total (quantity × unit price)
   - Insert line item with product details
9. **Response** - Return success confirmation with order details

## Workflow Features

### Data Transformation
- **Date Conversion**: YYYYMMDD (X12) → YYYY-MM-DD (PostgreSQL DATE)
- **Line Total Calculation**: Quantity × Unit Price
- **String Escaping**: Single quotes escaped for SQL safety
- **Null Handling**: Empty values properly handled

### Database Operations
- **Transactional Integrity**: Foreign key constraints ensure data consistency
- **Auto-generated IDs**: Serial primary keys for all tables
- **RETURNING Clause**: Get inserted purchase order ID for child records
- **Duplicate Prevention**: Unique constraint on PO number + control number

### Error Handling
The workflow will fail gracefully if:
- X12 message is invalid
- Database connection fails
- Duplicate purchase order number
- SQL constraint violations

## Useful SQL Queries

### Analytics Queries

**Total Orders by Date:**
```sql
SELECT
    order_date,
    COUNT(*) as order_count,
    SUM(total_line_items) as total_items
FROM x12_purchase_orders
GROUP BY order_date
ORDER BY order_date DESC;
```

**Orders by Trading Partner:**
```sql
SELECT
    sender_id,
    receiver_id,
    COUNT(*) as order_count,
    MIN(order_date) as first_order,
    MAX(order_date) as last_order
FROM x12_purchase_orders
GROUP BY sender_id, receiver_id;
```

**Top Products by Quantity:**
```sql
SELECT
    product_description,
    product_id,
    SUM(quantity) as total_quantity,
    COUNT(*) as order_count,
    SUM(line_total) as total_revenue
FROM x12_line_items
WHERE product_description IS NOT NULL
GROUP BY product_description, product_id
ORDER BY total_quantity DESC
LIMIT 10;
```

**Orders by Status:**
```sql
SELECT
    status,
    COUNT(*) as count,
    MIN(processed_at) as oldest,
    MAX(processed_at) as newest
FROM x12_purchase_orders
GROUP BY status;
```

## Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Errors
**Error:** "Cannot connect to PostgreSQL server"

**Solutions:**
- Verify firewall rules allow Logic App IP ranges
- Check connection string format
- Ensure database user has correct permissions
- For Azure PostgreSQL, use format: `username@servername`

#### 2. SQL Syntax Errors
**Error:** "Syntax error near..."

**Solutions:**
- Check single quote escaping in string values
- Verify date format conversions
- Ensure all required fields have values

#### 3. Duplicate Key Violations
**Error:** "duplicate key value violates unique constraint"

**Solutions:**
- Purchase order already exists in database
- Check unique constraint on `(purchase_order_number, transaction_set_control_number)`
- Either use different PO number or delete existing record

#### 4. Foreign Key Violations
**Error:** "violates foreign key constraint"

**Solutions:**
- Ensure purchase order is inserted before parties/line items
- Verify purchase order ID is correctly passed to child records

#### 5. Date Conversion Errors
**Error:** "invalid input syntax for type date"

**Solutions:**
- Verify X12 dates are in YYYYMMDD format
- Check date conversion expression in workflow
- Handle missing dates with NULL

### Debugging Tips

1. **Enable Logic App Run History**
   - View detailed execution logs
   - Check SQL query outputs
   - Verify data transformations

2. **Test SQL Queries Directly**
   - Run queries in pgAdmin or psql
   - Verify data is correctly formatted
   - Check for special characters

3. **Use Smaller Test Messages**
   - Start with `sample_x12_850_simple.x12`
   - Verify single line item insertion
   - Then test with full message

## Best Practices

### Performance
- **Indexes**: Schema includes indexes on frequently queried columns
- **Batch Processing**: For high volume, consider batch inserts
- **Connection Pooling**: PostgreSQL connector handles connection management

### Data Quality
- **Raw Data Storage**: Original X12 message stored for audit/replay
- **JSON Storage**: Decoded JSON stored as JSONB for flexible querying
- **Timestamps**: All records include creation timestamps

### Security
- **SQL Injection Prevention**: Use parameterized queries (note: current implementation uses string concatenation for demo purposes - consider using stored procedures in production)
- **Connection Security**: Use SSL for database connections
- **Credentials**: Store database credentials in Key Vault

### Monitoring
- **Status Field**: Track order processing status
- **Timestamps**: Monitor processing times
- **Audit Trail**: Complete history of all insertions

## Production Recommendations

For production use, consider:

1. **Use Stored Procedures** instead of inline SQL for better security and performance
2. **Implement Transactions** to ensure all-or-nothing insertions
3. **Add Error Logging Table** to track failed processing attempts
4. **Implement Retry Logic** for transient database failures
5. **Add Data Validation** before insertion
6. **Use Azure Key Vault** for database credentials
7. **Enable Application Insights** for monitoring and alerting
8. **Add Duplicate Detection** before insertion
9. **Implement Status Updates** (received → processing → completed)
10. **Create Backup Strategy** for database

## Next Steps

- **Demo 1**: Learn basic X12 decoding and JSON extraction
- **Demo 2**: Transform to internal order format for API integration
- **Demo 3**: Generate 997 Functional Acknowledgments
- **Demo 4**: Complete end-to-end B2B workflow with file processing

## Additional Resources

- [Azure Database for PostgreSQL Documentation](https://learn.microsoft.com/en-us/azure/postgresql/)
- [Logic Apps PostgreSQL Connector](https://learn.microsoft.com/en-us/connectors/postgresql/)
- [PostgreSQL SQL Reference](https://www.postgresql.org/docs/current/sql.html)
- [X12 850 Purchase Order Specification](https://www.stedi.com/edi/x12-004010/850)
- [Integration Account Setup Guide](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-enterprise-integration-create-integration-account)
