# Demo 2: Configuring Application Insights for Logic Apps and Functions

This demo focuses on wiring both **Logic Apps Standard** and **Azure Functions** to the same Application Insights instance so you can correlate runs, traces, and failures in one place.

## Goal
- Enable Application Insights telemetry for a Logic App Standard workflow.
- Enable Application Insights telemetry for an Azure Function.
- Validate logs with a simple KQL query.

## Prerequisites
- An Azure subscription with permission to create Application Insights resources.
- A Logic App Standard workflow (use `Day 9/Demo 1/error-handling-demo`).
- An Azure Function app (use `Day 9/Demo 3/custom-logging-function`).

## Step 1: Create Application Insights
1. In Azure Portal, create a new **Application Insights** resource.
2. Copy the **Connection string** from **Overview**.

## Step 2: Configure Logic App Standard
Add the connection string to the Logic App Standard **Configuration** settings:

- `APPLICATIONINSIGHTS_CONNECTION_STRING=<your-connection-string>`

Optional (legacy):
- `APPINSIGHTS_INSTRUMENTATIONKEY=<your-instrumentation-key>`

**Why this matters:** Logic Apps Standard will forward **run history**, **action failures**, and **trackedProperties** into Application Insights as traces and custom dimensions.

## Step 3: Configure Azure Functions
Add the same connection string to the Function App settings:

- `APPLICATIONINSIGHTS_CONNECTION_STRING=<your-connection-string>`

Optional (legacy):
- `APPINSIGHTS_INSTRUMENTATIONKEY=<your-instrumentation-key>`

For local runs, update `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "<your-connection-string>"
  }
}
```

## Step 4: Validate Telemetry
1. Run the Logic App and Function.
2. In Application Insights, open **Logs** and run:

```kusto
traces
| where message contains "error"
| order by timestamp desc
```

You should see both Logic App traces and Function logs when failures occur.

## Best-practice reminders
- Use **trackedProperties** in workflows to add correlation IDs and business context.
- Prefer **connection strings** over legacy instrumentation keys.
- Name resources consistently:
  - Logic Apps: `LA-ProjectName-WorkflowName`
  - Functions: `FA-ProjectName-FunctionName`

## Optional extra
- Add a **customDimension** like `correlationId` to both workflows and functions so you can filter cross-service telemetry easily.
