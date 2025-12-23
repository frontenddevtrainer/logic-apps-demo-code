# Hands-on Lab: Error Handling, Logging, and Best Practices

In this lab you will enhance a Logic App workflow with robust error handling, App Insights logging, and clear naming conventions.

## Objectives
1. Wrap main logic in a **Scope_Try** action.
2. Add a **Scope_Catch** that logs errors to Application Insights.
3. Send an email notification when a run fails.
4. Add **trackedProperties** for easier debugging.
5. Write a KQL query to find recent errors.

## Starter project
Use the completed workflow as a reference or starting point:
- `Day 9/Hands On/error-handling-hands-on/ErrorHandlingLab/workflow.json`

## Prerequisites
- An Application Insights resource.
- An Office 365 connection (or Outlook) for sending emails.
- The custom logger function from Demo 3 deployed or running locally:
  - `Day 9/Demo 3/custom-logging-function`

## Setup
1. Open `Day 9/Hands On/error-handling-hands-on` in VS Code.
2. Update `Day 9/Hands On/error-handling-hands-on/local.settings.json`:
   - `APPLICATIONINSIGHTS_CONNECTION_STRING`
   - `notificationEmail`
   - `loggerFunctionUrl`
   - `loggerFunctionKey`
3. Start the Logic App runtime:
   ```bash
   func start
   ```

## Exercise steps
### Step 1: Review the Try scope
- Check `Scope_Try` for the main logic and request validation.
- Confirm `trackedProperties` include `correlationId` and `orderId`.

### Step 2: Add the Catch scope
- Inspect `Scope_Catch` for:
  - `Compose_Error_Summary`
  - `Log_Error_to_App_Insights` (HTTP call to the logger function)
  - `Send_failure_notification` (Office 365 email)

### Step 3: Verify the Finally scope
- Confirm `Scope_Finally` always runs by checking `runAfter` statuses.

### Step 4: Run success and failure tests
```bash
# Success
curl -X POST "http://localhost:7071/api/ErrorHandlingLab" \
  -H "Content-Type: application/json" \
  -d '{"orderId":"PO-1001","sourceSystem":"lab"}'

# Failure
curl -X POST "http://localhost:7071/api/ErrorHandlingLab" \
  -H "Content-Type: application/json" \
  -d '{"orderId":"PO-1002","simulateFailure":true,"sourceSystem":"lab"}'
```

### Step 5: Query recent errors
In Application Insights **Logs**:

```kusto
traces
| where message contains "error"
| order by timestamp desc
```

## Best-practice checklist
- Workflow naming: `LA-ProjectName-WorkflowName`
- Function naming: `FA-ProjectName-FunctionName`
- Use `trackedProperties` for correlation ID and business identifiers.
- Avoid function keys in query strings; prefer Managed Identity in production.

## Validation
- Failure runs should show:
  - An email notification sent to `notificationEmail`.
  - A custom event in Application Insights from the logger function.
  - Tracked properties visible in the run history.
