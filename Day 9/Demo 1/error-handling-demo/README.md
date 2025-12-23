# Demo 1: Error Handling with Scope Actions

This demo shows a simple **try/catch/finally** pattern in a Logic App Standard workflow using Scope actions and `runAfter` conditions.

## What you get
- **Try scope**: main logic and a forced failure switch.
- **Catch scope**: captures the error payload from the failed scope.
- **Finally scope**: runs regardless of success or failure.
- **Tracked properties**: correlation-friendly metadata for run history and Application Insights.

## Files
- `Day 9/Demo 1/error-handling-demo/TryCatchDemo/workflow.json`
- `Day 9/Demo 1/error-handling-demo/host.json`
- `Day 9/Demo 1/error-handling-demo/local.settings.json`

## Run the demo
1. Open `Day 9/Demo 1/error-handling-demo` in VS Code.
2. Use **Logic Apps: Open Workflow Designer** to view the workflow.
3. Start the runtime with `func start` (optional for local run).
4. Trigger the workflow:

```bash
# Success path
curl -X POST "http://localhost:7071/api/TryCatchDemo" \
  -H "Content-Type: application/json" \
  -d '{"message":"demo run"}'

# Failure path
curl -X POST "http://localhost:7071/api/TryCatchDemo?forceFail=true" \
  -H "Content-Type: application/json" \
  -d '{"message":"demo run"}'
```

## What to point out live
- **`Scope_Try`** is the only scope with `runAfter: {}`. It owns the main logic.
- **`Scope_Catch`** uses `runAfter` with `Failed` and `TimedOut` to act like `catch`.
- **`Scope_Finally`** uses `runAfter` with `Succeeded`, `Failed`, `TimedOut`, and `Skipped` to emulate `finally`.
- **Tracked properties** are attached to scopes to log `correlationId` for easier investigation.

## Naming best practices
- Workflows: `LA-ProjectName-WorkflowName`
- Functions: `FA-ProjectName-FunctionName`
- Actions: `Scope_Try`, `Scope_Catch`, `Scope_Finally` for predictable run history.
