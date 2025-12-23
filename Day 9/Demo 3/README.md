# Demo 3: Custom Logging with trackEvent and trackException

This demo adds a lightweight **logging helper function** that accepts JSON and writes custom telemetry to Application Insights using `track_event` and `track_exception`.

## What you get
- A Python Azure Function (`custom-logger`) that logs **events** and **exceptions**.
- Correlation-friendly properties so Logic Apps and Functions can share a `correlationId`.

## Files
- `Day 9/Demo 3/custom-logging-function/function_app.py`
- `Day 9/Demo 3/custom-logging-function/requirements.txt`
- `Day 9/Demo 3/custom-logging-function/local.settings.json`

## Configure Application Insights
Update `Day 9/Demo 3/custom-logging-function/local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "<your-connection-string>"
  }
}
```

## Run locally
```bash
cd "Day 9/Demo 3/custom-logging-function"
func start
```

## Send a test event
```bash
curl -X POST "http://localhost:7071/api/custom-logger?code=<function-key>" \
  -H "Content-Type: application/json" \
  -d '{
        "eventName": "LogicAppFailure",
        "correlationId": "demo-123",
        "properties": {
          "workflowName": "LA-ErrorHandling-TryCatch",
          "orderId": "PO-7781",
          "sourceSystem": "demo"
        },
        "exceptionMessage": "Simulated failure for demo",
        "exceptionType": "ForcedFailure",
        "severityLevel": 3
      }'
```

## Validate in Application Insights
Use **Logs** in the App Insights resource:

```kusto
customEvents
| where name == "LogicAppFailure"
| order by timestamp desc
```

```kusto
exceptions
| order by timestamp desc
```

## Live demo talking points
- `track_event` captures **custom business signals** (e.g., failed order IDs).
- `track_exception` captures **errors** and stacks for diagnostics.
- `correlationId` makes it easy to join Logic App runs and Function traces.

## Best-practice reminders
- Use **Function auth level** + managed identity for production.
- Keep **sensitive values** (keys, connection strings) in app settings.
- Name Functions consistently: `FA-ProjectName-FunctionName`.
