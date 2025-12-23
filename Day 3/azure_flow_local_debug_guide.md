## Azure Logic Apps: Export, Run Locally, and Debug

This guide walks through exporting a Logic App **Standard (single-tenant)** from Azure
and continuing development locally with debugging.

> Note: I cannot access the network from this environment to verify the latest docs.
> Use this as a clean baseline, then cross-check with the current Microsoft docs if
> anything has changed.

---

## 1. Prerequisites (Standard)

- VS Code
- Azure Logic Apps (Standard) extension for VS Code
- Azure Functions Core Tools v4
- Node.js LTS (required by Core Tools)
- .NET 6+ and PowerShell 7 (for some built-in connectors and tools)

Optional but recommended:

- Azure CLI (for alternative export paths)
- Storage account connection string (local or Azure)

---

## 2. Confirm Your Logic App Is Standard

In Azure Portal, verify the resource type is **Logic App (Standard)**.

---

## 3. Export a Logic App Standard Project

### Option A: VS Code (Recommended)

1. Open VS Code.
2. Install and sign in with the Azure Logic Apps (Standard) extension.
3. Open the Azure sidebar and expand your subscription.
4. Find your Logic App (Standard).
5. Choose **Download** (or **Download from Azure**).
6. Select a local folder.

This pulls:

- `workflows/<workflowName>/workflow.json`
- `connections.json`
- `local.settings.json` (or a template)
- `host.json`, `appsettings.json` (if present)

### Option B: Azure Portal

1. Navigate to the Logic App (Standard).
2. Open **Workflows**.
3. Select a workflow.
4. Use **Download** in the designer toolbar (if available).

Portal export typically downloads the workflow definition, but VS Code is best for a
full project with settings and connections.

---

## 4. Set Up Local Settings

Create or update `local.settings.json` with:

- `AzureWebJobsStorage`
- Any app settings referenced by your workflow (e.g., `@appsetting('KEY')`)

Example (redact secrets before committing):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "WORKFLOW_ENV": "local",
    "API_BASE_URL": "https://api.example.com"
  }
}
```

If your workflow uses connectors, ensure `connections.json` exists and is correct for
local use.

---

## 5. Run Locally

From the Logic App project root:

```bash
func start
```

Expected:

- The Functions host starts.
- The workflow endpoints are listed in the output.

If you have multiple workflows, each workflow has its own route.

---

## 6. Debug in VS Code

1. Open the Logic App project folder in VS Code.
2. Go to **Run and Debug**.
3. Select **Attach to Logic App (Standard)** (or the provided launch config).
4. Press **F5**.
5. Trigger your workflow using Postman, curl, or a built-in trigger.

Set breakpoints in custom code:

- Inline code in workflows (JavaScript)
- Azure Functions or API apps the workflow calls

---

## 7. Common Pitfalls

- Missing `AzureWebJobsStorage` in `local.settings.json`.
- Using a connector that requires a managed identity not available locally.
- `connections.json` still pointing to Azure-only resources.
- Using a trigger/action not supported in Standard.

---

## 8. Suggested Workflow for Ongoing Development

1. Download from Azure to local.
2. Update settings and connections for local.
3. Run `func start`.
4. Debug and iterate.
5. Publish back to Azure from VS Code when ready.
