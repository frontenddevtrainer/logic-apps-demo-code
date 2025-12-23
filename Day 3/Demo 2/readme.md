# Demo 2: Azure Function with Transaction Management and Rollback
## Python Azure Function (v2 Programming Model) + Azure PostgreSQL Flexible Server
### End-to-End Guide + Issues & Fixes

This demo demonstrates how to implement **explicit database transaction management** using the **Azure Functions Python v2 programming model**, including **commit, rollback, and validation-based failure handling** with **Azure Database for PostgreSQL – Flexible Server**.

This demo complements **Demo 1 (Logic Apps batching)** by showing when **full transactional control** is required.

---

## 1. What This Demo Achieves

- Runs **Azure Functions locally**
- Uses **Python v2 programming model**
- Implements **explicit BEGIN / COMMIT / ROLLBACK**
- Connects to **Azure PostgreSQL Flexible Server**
- Ensures **atomic inserts**
- Prevents **partial writes**
- Demonstrates **rollback on validation failure**

---

## 2. When to Use This Pattern

Use **Azure Functions** instead of Logic Apps when:

| Requirement | Supported |
|-----------|-----------|
Multi-row atomic writes | ✅ |
Rollback on error | ✅ |
Complex validation | ✅ |
High-volume ingestion | ✅ |
Low-code orchestration | ❌ |

---

## 3. Prerequisites

- Python **3.9 – 3.11**
- Azure Functions Core Tools **v4**
- Node.js **LTS**
- Visual Studio Code
- Azure PostgreSQL Flexible Server

```bash
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

### VS Code Extensions
- Azure Functions
- Azure Account

---

## 4. Create Azure Function Project

```bash
func init demo-2 --python
cd demo-2
```

This creates a project using the **Python v2 programming model**.

---

## 5. Project Structure (IMPORTANT)

```text
demo-2/
├── .vscode/
├── .gitignore
├── function_app.py      # Main entry point (v2 model)
├── host.json
├── local.settings.json
├── requirements.txt
```

### ⚠️ Notes
- There are **no per-function folders**
- There is **no function.json**
- All functions are declared in `function_app.py`

This is **expected and correct**.

---

## 6. PostgreSQL Setup

```sql
CREATE SCHEMA IF NOT EXISTS logicapp;

CREATE TABLE IF NOT EXISTS logicapp.messages (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Ensure the database user has **INSERT** privileges.

---

## 7. Python Dependencies

### requirements.txt
```txt
psycopg2-binary
```

---

## 8. local.settings.json

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PG_HOST": "<your-host>.postgres.database.azure.com",
    "PG_DB": "<database-name>",
    "PG_USER": "<username>",
    "PG_PASSWORD": "<password>",
    "PG_PORT": "5432"
  }
}
```

---

## 9. Azure Function Code (Transaction + Rollback)

### function_app.py

```python
import json
import logging
import os
import psycopg2
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="transaction-demo")
@app.route(route="transaction-demo", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def transaction_demo(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        records = body.get("records", [])

        if not records:
            return func.HttpResponse(
                json.dumps({"error": "No records provided"}),
                status_code=400,
                mimetype="application/json"
            )

        conn = psycopg2.connect(
            host=os.environ["PG_HOST"],
            database=os.environ["PG_DB"],
            user=os.environ["PG_USER"],
            password=os.environ["PG_PASSWORD"],
            port=os.environ["PG_PORT"],
            sslmode="require"
        )

        conn.autocommit = False
        cursor = conn.cursor()

        for record in records:
            if "email" not in record:
                raise Exception("Validation failed: email missing")

            cursor.execute(
                """
                INSERT INTO logicapp.messages (email, message)
                VALUES (%s, %s)
                """,
                (record["email"], record.get("message"))
            )

        conn.commit()

        return func.HttpResponse(
            json.dumps({
                "status": "committed",
                "count": len(records)
            }),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Transaction failed: {str(e)}")

        if "conn" in locals():
            conn.rollback()

        return func.HttpResponse(
            json.dumps({
                "status": "rolled_back",
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()
```

---

## 10. Run Demo 2 Locally

```bash
pip install -r requirements.txt
func start
```

Expected output:
```
Found Python functions:
  transaction-demo
```

---

## 11. Test the Function

### Successful Commit

```bash
curl -X POST http://localhost:7071/api/transaction-demo   -H "Content-Type: application/json"   -d '{
    "records": [
      { "email": "a@test.com", "message": "hello" },
      { "email": "b@test.com", "message": "world" }
    ]
  }'
```

✔ All rows inserted  
✔ Transaction committed  

---

### Rollback Scenario

```bash
curl -X POST http://localhost:7071/api/transaction-demo   -H "Content-Type: application/json"   -d '{
    "records": [
      { "email": "a@test.com", "message": "ok" },
      { "message": "this will fail" }
    ]
  }'
```