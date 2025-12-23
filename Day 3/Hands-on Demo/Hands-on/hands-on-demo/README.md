## Hands-on Logic Apps Demo

This project contains a **Stateful Logic App Standard** workflow (`demo/workflow.json`) that ingests CSV files over HTTP, validates the content, and prepares batched persistence actions (query steps left as placeholders so you can bind them to your own PostgreSQL actions in the designer).

### Prerequisites

- Azure subscription with permission to create Logic Apps Standard resources.
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local#install-the-azure-functions-core-tools) v4 (required for running Logic Apps Standard locally).
- [Visual Studio Code](https://code.visualstudio.com/) with the **Azure Logic Apps (Standard)** extension (recommended) or the Azure CLI for deployment.
- PostgreSQL database/tables that match the workflow’s expected schema (e.g., `public.import_data`, `public.import_errors`).

### Repository Layout

| Path | Purpose |
| ---- | ------- |
| `demo/workflow.json` | Main workflow definition. Placeholder `Compose` actions mark where database inserts should be reintroduced in the designer. |
| `workflow-designtime/` | Logic App designer metadata. |
| `host.json`, `local.settings.json` | Logic App runtime configuration for local execution. |
| `lib/`, `Artifacts/` | Supporting assets created by the Logic Apps tooling. |

### Sample Data & Schema

**CSV Example** – see [`sample-data/sample.csv`](./sample-data/sample.csv)

**PostgreSQL Schema**

```sql
CREATE TABLE public.import_data (
    customer_id uuid NOT NULL,
    email text NOT NULL,
    amount numeric(18,2) NOT NULL,
    imported_at timestamptz NOT NULL
);

CREATE TABLE public.import_errors (
    id bigserial PRIMARY KEY,
    source_file text NOT NULL,
    row_number int,
    payload jsonb,
    error_reason text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

The workflow expects the `import_data` and `import_errors` tables (or equivalent) to exist so the PostgreSQL actions you add in the designer have a target schema.

### Running the Workflow Locally

1. **Install dependencies**  
   ```bash
   npm install -g @azure/functions-core-tools@4 --unsafe-perm true
   ```
   (Skip if you already have Core Tools v4.)

2. **Configure connections and secrets**  
   - Open `local.settings.json` and add any required connection strings or environment settings (for example, PostgreSQL connection info) that your workflow actions will use once you reintroduce them in the designer.

3. **Start the Logic App Standard runtime**  
   ```bash
   func start
   ```
   The runtime hosts the workflow endpoints locally (you’ll see a generated URL for the `Receive_Csv_File` trigger).

4. **Trigger the workflow**  
   Use `curl` or Postman to POST a CSV payload to the local callback URL:
   ```bash
   curl -X POST "http://localhost:7071/api/Receive_Csv_File?code=<key>" \
        -H "Content-Type: application/json" \
        -d '{
              "fileName": "sample.csv",
              "content": "customer_id,email,amount,imported_at\nc5f184d5-6095-49c4-92f3-767b7f873a87,grace@example.com,125.50,2024-04-15T10:00:00Z"
            }'
   ```
   Adjust the `code` query parameter to match the shared access signature printed by Core Tools.

### Editing the Workflow

1. Launch VS Code and install the *Azure Logic Apps (Standard)* extension if you haven’t already.
2. Open this folder (`Hands-on/hands-on-demo`) and press `Ctrl+Shift+P` → `Logic Apps: Open Workflow Designer`.
3. Re-add PostgreSQL “Insert row” / “Execute query” actions in place of the `Compose` placeholders labeled `actionNote`. Configure these connections using your Azure resources.
4. Save the workflow; the extension updates `demo/workflow.json`.

### Deploying to Azure

1. Create a Logic App Standard instance in the target resource group/region.
2. From VS Code, right-click the project and choose **Deploy to Logic App (Standard)**, or use the Azure CLI:
   ```bash
   az logicapp deployment source config-zip \
     --resource-group <rg> \
     --name <logic-app-name> \
     --src Hands-on/hands-on-demo.zip
   ```
3. Reconfigure managed connections (PostgreSQL, etc.) in the Azure Portal so the workflow actions run with production credentials.

### Verifying End-to-End

After deployment:
1. Grab the HTTP trigger URL from the Logic App Portal.
2. Send a CSV payload as shown earlier.  
3. Check the run history for success, inspect variables (`ValidRecords`, `InvalidRecords`, `FailedBatchRecords`), and ensure your database tables receive the expected inserts once you wire up the actual actions.

### Troubleshooting

- **`InternalServerError` during save/run**: Usually caused by missing or misconfigured managed connections. Replace placeholder actions with real connectors and authenticate them in the designer.
- **Variable or action validation errors**: Logic Apps only allows `InitializeVariable` at the top level. Keep them outside scopes/conditions (already handled in this project).
- **CSV parsing issues**: Ensure the uploaded payload uses `customer_id,email,amount,imported_at` headers and `\n` line endings; otherwise the workflow flags rows as invalid.

Feel free to adapt the workflow (change headers, validation rules, batch size, etc.) to match your use case once the baseline functionality is verified.
