# Demo 3: Configuring Retry Policies on PostgreSQL Actions with Azure Functions
## HTTP-triggered Azure Function (Python v2) + Azure Database for PostgreSQL

This demo shows how to combine **Azure Functions host-level retries** with a **custom retry policy at the database action level** to make PostgreSQL calls resilient to transient failures (TLS renegotiation, network blips, serialization errors, etc.).

The sample function accepts an HTTP `POST` request that contains records for insertion.  
It uses:

- `@app.route(..., retry=func.RetryPolicy(...))` to tell the **Azure Functions runtime** how to re-run the function if it keeps raising retryable errors.
- A `execute_with_retry()` helper that wraps the PostgreSQL insert logic with **exponential backoff** to smooth over transient database exceptions before the host needs to re-trigger the whole function.

Use this pattern when you want **fine-grained control** over how many times a PostgreSQL action is attempted before surfacing an error back to the workflow (Logic App, Durable Function, Event Grid, etc.).

---

## 1. Scenario

- Azure Function receives a batch of email payloads.
- Function inserts each payload into `logicapp.retry_messages`.
- Any transient PostgreSQL error is retried up to `PG_ACTION_MAX_ATTEMPTS` times with exponential backoff.
- If the action still fails, the function raises the exception so that the **host-level retry policy** can re-run the entire invocation.
- After the final retry fails, the logic app (or caller) gets a deterministic HTTP 500 with details for troubleshooting.

---

## 2. When to Use This Pattern

| Requirement | Addressed in this demo |
| --- | --- |
| Control PostgreSQL retries independently from Logic Apps | ✅ |
| Exponential backoff with jitter-like caps | ✅ |
| Host-level retries managed by Azure Functions | ✅ |
| Clear observability of attempt counts | ✅ |
| Long-running transactional batch | ❌ (see Demo 2) |

---

## 3. Project Layout

```
Day 3/Demo 3/
├── function_app.py          # HTTP trigger + retry logic
├── host.json                # function runtime limits
├── local.settings.json      # local secrets + retry knobs
├── requirements.txt         # dependencies (azure-functions, psycopg2-binary)
└── README.md
```

All logic lives inside `function_app.py` using the **Python v2 programming model** (no per-function folders or `function.json` files).

---

## 4. PostgreSQL Setup

```sql
CREATE SCHEMA IF NOT EXISTS logicapp;

CREATE TABLE IF NOT EXISTS logicapp.retry_messages (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

Ensure the function's database principal has `INSERT` permissions for this table.

---

## 5. Configure Retries

### 5.1 Host-Level Retry (Azure Functions runtime)

`function_app.py` defines:

```python
host_retry_policy = func.RetryPolicy(
    max_retry_attempts=3,
    delay_interval=timedelta(seconds=5),
    maximum_delay_interval=timedelta(seconds=20),
    strategy=func.RetryStrategy.EXPONENTIAL_BACKOFF,
)
```

and applies the policy:

```python
@app.route(..., retry=host_retry_policy)
```

- The runtime will **re-run the entire function invocation** (with the same request data) if the function raises `OperationalError`, `DeadlockDetected`, etc.
- Use environment variables (`HOST_MAX_RETRY_ATTEMPTS`, `HOST_RETRY_DELAY_SECONDS`, `HOST_MAX_RETRY_DELAY_SECONDS`) to tune the behavior without code edits.

### 5.2 Action-Level Retry (custom psycopg2 logic)

`execute_with_retry()` wraps the insert operation:

```python
attempts = execute_with_retry(operation)
```

- Retries only the PostgreSQL action, not the full Azure Function.
- Uses exponential backoff bounded by `PG_ACTION_BASE_DELAY_SECONDS` and `PG_ACTION_MAX_DELAY_SECONDS`.
- Guards against `OperationalError`, `SerializationFailure`, `DeadlockDetected`, etc.
- Surfaces the number of database attempts back to the caller (`dbAttempts` property in the response) so you can observe how often Logic Apps is running on transient failures.

---

## 6. Prerequisites

- Python **3.9 – 3.11**
- Azure Functions Core Tools **v4**
- Node.js **LTS** (required by Core Tools)
- VS Code with the **Azure Functions** and **Azure Account** extensions
- Access to an **Azure Database for PostgreSQL Flexible Server**

Install Core Tools if you don't have them:

```bash
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

Install Python requirements:

```bash
pip install -r requirements.txt
```

> This installs `debugpy` (needed for VS Code debugging) and pins `azure-functions==1.21.3`, which includes the `RetryPolicy` API used by this sample.
>
> If you run on an older Core Tools bundle that lacks `RetryPolicy`, the function still runs; it simply skips the host-level retry decoration while keeping the custom psycopg2 retry logic.

---

## 7. Configure `local.settings.json`

Update the placeholders before running locally:

```jsonc
{
  "Values": {
    "PG_HOST": "demo-flexible.postgres.database.azure.com",
    "PG_DB": "logicappdemo",
    "PG_USER": "demo@demo-flexible",
    "PG_PASSWORD": "<strong-password>",
    "PG_PORT": "5432",
    "PG_SSLMODE": "require",
    "PG_CONNECT_TIMEOUT": "10",
    "PG_ACTION_MAX_ATTEMPTS": "4",
    "PG_ACTION_BASE_DELAY_SECONDS": "1.5",
    "PG_ACTION_MAX_DELAY_SECONDS": "15",
    "HOST_MAX_RETRY_ATTEMPTS": "3",
    "HOST_RETRY_DELAY_SECONDS": "5",
    "HOST_MAX_RETRY_DELAY_SECONDS": "20"
  }
}
```

> `PG_ACTION_MAX_ATTEMPTS` represents how many times the **database action** will retry before giving up.  
> Once the action throws, it bubbles up to the Azure Functions runtime, which applies the host-level retry policy.

---

## 8. Run the Azure Function Locally

```bash
func start
```

Expected output:

```
Found Python functions:
        pg-retry-demo
```

---

## 9. VS Code Launch & Debugging

For a full debugging experience, this demo ships with its own `.vscode` folder (`Day 3/Demo 3/.vscode`).  
Open **Day 3/Demo 3** as your workspace (or add it as an additional folder in a multi-root workspace) so VS Code can pick up these files, then:

1. Open the **Run and Debug** panel in VS Code.
2. Select the configuration **“Day 3 Demo 3 - Debug Azure Function.”**
3. Press **F5**. VS Code runs the new task `func: start Day 3 Demo 3`, which:
   - Executes `func start` from `Day 3/Demo 3`.
   - Sets `languageWorkers__python__arguments` so the Python worker waits for the debugger on port `9091`.
4. VS Code automatically attaches the Python debugger once the worker signals readiness.

When you're done, stop debugging (`Shift+F5`) which terminates the running host in the dedicated terminal.

You can also run the task manually from the terminal (`Terminal → Run Task… → func: start Day 3 Demo 3`) if you only need to observe logs without attaching.

---

## 10. Test Scenarios

### 10.1 Successful Insert (no retries)

```bash
curl -X POST http://localhost:7071/api/pg-retry-demo \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"email": "a@example.com", "message": "hello"},
      {"email": "b@example.com", "message": "world"}
    ]
  }'
```

Sample response:

```json
{
  "status": "success",
  "inserted": 2,
  "dbAttempts": 1,
  "hostRetryConfigured": true
}
```

### 10.2 Simulate Transient Failures (action-level retries)

The request body supports a helper flag to simulate connection drops before touching PostgreSQL. This is useful when presenting the demo even if the database is perfectly healthy.

```bash
curl -X POST http://localhost:7071/api/pg-retry-demo \
  -H "Content-Type: application/json" \
  -d '{
    "simulateTransientErrors": 2,
    "records": [
      {"email": "c@example.com", "message": "transient sample"}
    ]
  }'
```

The function will raise `OperationalError` twice, back off (`1.5s`, then `3s`), and eventually succeed:

```json
{
  "status": "success",
  "inserted": 1,
  "dbAttempts": 3,
  "hostRetryConfigured": true
}
```

Logs show the retry loop:

```
Transient PostgreSQL error 'Simulated transient connection reset.' (attempt 1/4). Retrying in 1.5 seconds.
Transient PostgreSQL error 'Simulated transient connection reset.' (attempt 2/4). Retrying in 3.0 seconds.
```

### 10.3 Force Host-Level Retry

If the database is down long enough that the custom action retries exhaust themselves, the function raises the last PostgreSQL exception, triggering the Azure Functions runtime to reschedule the invocation according to `host_retry_policy`. After all host attempts are spent, the caller receives HTTP 500.

You can simulate this by setting `PG_ACTION_MAX_ATTEMPTS=1` temporarily or stopping the PostgreSQL server before running the request.

---

## 11. Integrating with Logic Apps

1. Use the **HTTP action** in your Logic App Standard/Consumption workflow.
2. Point it at the deployed Azure Function.
3. Configure the Logic App's own retry policy to `None` so you can observe Azure Function level retries, or leave the defaults if you want retries across all layers.
4. Monitor:
   - `dbAttempts` in the HTTP response
   - Azure Function Application Insights traces (`Transient PostgreSQL error...`)
   - PostgreSQL server metrics (connections, failures)

This gives you a complete story:

| Layer | What it handles |
| --- | --- |
| PostgreSQL client (`execute_with_retry`) | Deadlocks, TLS renegotiation, serialization failures |
| Azure Functions retry policy | Cold-start/host errors, consistent resubmission of the HTTP call |
| Logic App retry policy (optional) | Network issues between Logic Apps and the Azure Function |

---

## 12. Clean Up

- Stop the Azure Function: `Ctrl + C` (or `func host stop`).
- Drop the `logicapp.retry_messages` table if you no longer need it.
- Remove secrets from `local.settings.json` before checking into source control.

---

## 13. Troubleshooting Tips

- `psycopg2.OperationalError: connection timeout` immediately → verify firewall or VNet integration.
- Logs mention `retry attempts exhausted` → raise `PG_ACTION_MAX_ATTEMPTS` or review the PostgreSQL availability.
- Azure Function keeps restarting → check `func --version` and that you're using Python 3.9–3.11.

---

Happy demoing! This scenario is ideal for illustrating **resilience layering**: PostgreSQL client retries, Azure Functions host retries, and optional Logic App retries. Together they protect mission-critical workflows from transient issues without duplicating inserts.
