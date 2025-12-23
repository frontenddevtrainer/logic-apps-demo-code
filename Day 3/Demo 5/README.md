# Demo 5: Rollback with Stored Procedure
## Azure Function + PostgreSQL Stored Procedure Transactions

This demo builds on Demo 2, but moves the multi-row insert logic into a **PostgreSQL stored procedure**. The Azure Function simply invokes the stored procedure inside an explicit transaction. If the stored procedure raises an exception—or if the function encounters any error afterwards—the entire batch is **rolled back**.

---

## 1. Scenario

1. Logic App (or any HTTP caller) posts an array of email/message records to the Azure Function.
2. The Python Azure Function (v2 programming model) opens a PostgreSQL transaction.
3. It calls a stored procedure: `logicapp.insert_messages_batch(jsonb_records)`.
4. The procedure loops through the JSON array and performs validation + INSERT statements.
5. If any record is invalid, the procedure raises an exception. The Azure Function rolls back.
6. If the function is asked to simulate a downstream failure (**after** the procedure completes), it throws an error so you can demonstrate that even post-procedure issues roll back the work.

---

## 2. When to Use This Pattern

| Requirement | Covered |
| --- | --- |
| Centralized database logic (auditing, defaults, constraints) | ✅ |
| Full rollback across multiple statements | ✅ |
| Logic Apps + Azure Functions integration | ✅ |
| Graceful error reporting to caller | ✅ |
| Cross-database logic | ❌ |

---

## 3. PostgreSQL Setup

Run the following script once on your PostgreSQL Flexible Server (or Single Server) instance:

```sql
CREATE SCHEMA IF NOT EXISTS logicapp;

CREATE TABLE IF NOT EXISTS logicapp.proc_messages (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE PROCEDURE logicapp.insert_messages_batch(records JSONB)
LANGUAGE plpgsql
AS $$
DECLARE
    rec JSONB;
BEGIN
    FOR rec IN SELECT * FROM jsonb_array_elements(records)
    LOOP
        IF NOT rec ? 'email' THEN
            RAISE EXCEPTION 'Validation failed: email missing';
        END IF;

        INSERT INTO logicapp.proc_messages (email, message)
        VALUES (rec->>'email', COALESCE(rec->>'message', ''));
    END LOOP;
END;
$$;
```

Feel free to extend the procedure with more business rules, logging, or auditing logic.

---

## 4. Project Layout

```
Day 3/Demo 5/
├── function_app.py          # HTTP trigger calling the stored procedure
├── host.json
├── local.settings.json      # sample values; do not commit secrets
├── requirements.txt
└── README.md
```

Everything lives inside a single `function_app.py` module using the Azure Functions Python v2 programming model (no `function.json` files).

---

## 5. Configuration (`local.settings.json`)

```jsonc
{
  "Values": {
    "PG_HOST": "demo-flexible.postgres.database.azure.com",
    "PG_DB": "logicappdemo",
    "PG_USER": "demo@demo-flexible",
    "PG_PASSWORD": "<strong-password>",
    "PG_PORT": "5432",
    "PG_SSLMODE": "require",
    "PG_INSERT_PROC": "logicapp.insert_messages_batch"
  }
}
```

> `PG_INSERT_PROC` lets you point to a different stored procedure without touching code (schema-qualified name recommended).

---

## 6. Install Dependencies

```bash
cd "Day 3/Demo 5"
python -m venv .venv            # optional but recommended
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 7. Run the Function Locally

```bash
func start
```

Expected output:

```
Found Python functions:
        stored-proc-rollback
```

---

## 8. Test the Stored Procedure Path

### 8.1 Successful Batch

```bash
curl -X POST http://localhost:7071/api/stored-proc-rollback \
  -H "Content-Type: application/json" \
  -d '{
        "records": [
          {"email": "batch1@example.com", "message": "hello"},
          {"email": "batch2@example.com", "message": "world"}
        ]
      }'
```

Sample response:

```json
{
  "status": "committed",
  "inserted": 2,
  "procedure": "logicapp.insert_messages_batch"
}
```

Check `logicapp.proc_messages` to see both rows inserted.

### 8.2 Stored Procedure Validation Failure

The procedure raises an exception if a record is missing `email`.

```bash
curl -X POST http://localhost:7071/api/stored-proc-rollback \
  -H "Content-Type: application/json" \
  -d '{
        "records": [
          {"email": "ok@example.com", "message": "ok"},
          {"message": "this will fail"}
        ]
      }'
```

Response:

```json
{
  "status": "rolled_back",
  "error": "Validation failed: email missing"
}
```

No rows are committed to the table.

### 8.3 Simulate Downstream Failure

Use `simulateFailure` to create an exception **after** the stored procedure completes. This proves that you can roll back even when the procedure itself succeeds but a later step in the Azure Function fails.

```bash
curl -X POST http://localhost:7071/api/stored-proc-rollback \
  -H "Content-Type: application/json" \
  -d '{
        "simulateFailure": true,
        "records": [
          {"email": "should-not-stick@example.com", "message": "rollback me"}
        ]
      }'
```

Response:

```json
{
  "status": "rolled_back",
  "error": "simulateFailure=true triggered an exception after the stored procedure call."
}
```

Verify that the table still has no additional rows.

---

## 9. Deployment Tips

1. Provision an Azure Function App (Linux/Python 3.11 recommended) and configure the same PG_* settings in Application Settings.
2. Deploy via VS Code, Azure CLI (`func azure functionapp publish`), or CI/CD.
3. Point your Logic App HTTP action to the deployed function URL.
4. Optional: enable Managed Identity in the Function App and use Azure AD authentication for PostgreSQL Flexible Server to avoid storing passwords.

---

## 10. Troubleshooting

- **`ModuleNotFoundError: psycopg2`** – Make sure `pip install -r requirements.txt` ran in the same environment as `func start`.
- **`Validation failed: email missing`** – The stored procedure intentionally enforces that field. Provide it in every record.
- **Timeouts** – Increase PostgreSQL `connect_timeout` by adding it to `_connection_params()` if needed, or verify firewall/VNet integration.
- **Permission errors** – Ensure the database login can execute the stored procedure and insert into `logicapp.proc_messages`.

---

You now have a reusable pattern showing how to push business logic into PostgreSQL stored procedures while still getting full transactional guarantees and clean rollback semantics from Azure Functions.
