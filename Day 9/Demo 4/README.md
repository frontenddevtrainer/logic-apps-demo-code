# Demo 4: Build a Simple Monitoring Dashboard in Azure Portal

This demo shows how to create a lightweight **monitoring dashboard** that surfaces Logic App failures and Function telemetry.

## Step 1: Open Application Insights
1. Go to the Application Insights resource connected to your Logic App and Function.
2. Select **Logs**.

## Step 2: Add key queries
Run and pin each query to a dashboard.

### Recent errors (traces)
```kusto
traces
| where message contains "error"
| order by timestamp desc
```

### Exceptions
```kusto
exceptions
| order by timestamp desc
```

### Failed requests
```kusto
requests
| where success == false
| project timestamp, name, resultCode, duration, operation_Id
| order by timestamp desc
```

### Custom events from the logger function
```kusto
customEvents
| where name == "LogicAppFailure"
| project timestamp, name, customDimensions
| order by timestamp desc
```

## Step 3: Pin to a dashboard
1. For each query, click **Pin**.
2. Choose **New dashboard** (or an existing one).
3. Name it `LA-ErrorHandling-Monitoring` (example).

## Step 4: Add a summary chart
Use a simple time chart to track errors over time:

```kusto
customEvents
| where name == "LogicAppFailure"
| summarize failures = count() by bin(timestamp, 1h)
| render timechart
```

## Step 5: Add filters
- Filter by `customDimensions.correlationId` when investigating a specific run.
- Filter by `cloud_RoleName` to isolate Logic App vs Function telemetry.

## What to call out in the demo
- Dashboard tiles update live as new failures occur.
- You can drill into a single run using `operation_Id` and `correlationId`.
- Pinning KQL queries turns ad-hoc troubleshooting into an operational view.
