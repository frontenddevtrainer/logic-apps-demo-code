# Logic App (Standard) Local Development Guide

This guide explains how to run and test the Logic App locally before deploying to Azure.

## Prerequisites

### 1. Install Required Tools

```bash
# Azure Functions Core Tools (v4)
brew install azure-functions-core-tools@4

# Or on Windows
winget install Microsoft.Azure.FunctionsCoreTools

# Or via npm
npm install -g azure-functions-core-tools@4
```

### 2. Install Azurite (Local Storage Emulator)

```bash
# Via npm
npm install -g azurite

# Or via Docker
docker pull mcr.microsoft.com/azure-storage/azurite
```

### 3. Install VS Code Extensions (Recommended)

- [Azure Logic Apps (Standard)](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurelogicapps)
- [Azurite](https://marketplace.visualstudio.com/items?itemName=Azurite.azurite)

## Project Structure

```
final-project-logic-app/
├── final-project-logic-app/
│   ├── .vscode/
│   │   ├── extensions.json
│   │   ├── launch.json
│   │   ├── settings.json
│   │   └── tasks.json
│   ├── FinalProject/              # Workflow folder
│   │   └── workflow.json          # Workflow definition
│   ├── workflow-designtime/
│   │   ├── host.json
│   │   └── local.settings.json
│   ├── .funcignore
│   ├── .gitignore
│   ├── host.json
│   └── local.settings.json
└── final-project-logic-app.code-workspace
```

## Running Locally

### Step 1: Start the Storage Emulator

Open a terminal and start Azurite:

```bash
# Start all Azurite services (blob, queue, table)
azurite --silent --location /tmp/azurite --debug /tmp/azurite/debug.log

# Or start only blob storage
azurite-blob --silent --location /tmp/azurite
```

**Using Docker:**
```bash
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 \
  mcr.microsoft.com/azure-storage/azurite
```

### Step 2: Configure Local Settings

Ensure `local.settings.json` has the correct configuration:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "dotnet",
    "APP_KIND": "workflowapp",
    "FUNCTIONS_INPROC_NET8_ENABLED": "1",
    "functionAppUrl": "http://localhost:7072/api/process-order"
  }
}
```

> **Note:** If you're also running the Azure Function locally, update `functionAppUrl` to point to your local function endpoint.

### Step 3: Start the Logic App

```bash
cd "Day 7/Final Project/final-project-logic-app/final-project-logic-app"

# Start the Logic App runtime
func start --port 7071
```

You should see output like:
```
Azure Functions Core Tools
Core Tools Version: 4.x

Functions:
  FinalProject: http://localhost:7071/api/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/invoke
```

### Step 4: Test the Workflow

Send a test request to the Logic App:

```bash
curl -X POST "http://localhost:7071/api/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*PO-TEST-001**20240115~N1*BY*Test Corp*92*TEST-001~PO1*001*5*EA*99.99*PE*VP*PROD-001~CTT*1*5~SE*6*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }'
```

## Running with the Azure Function Locally

To test the complete flow (Logic App calling Function App):

### Terminal 1: Start the Azure Function
```bash
cd "Day 7/Final Project/order-processing-function"

# Create virtual environment (first time only)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the function
func start --port 7072
```

### Terminal 2: Start Azurite
```bash
azurite --silent --location /tmp/azurite
```

### Terminal 3: Start the Logic App
```bash
cd "Day 7/Final Project/final-project-logic-app/final-project-logic-app"
func start --port 7071
```

### Test the Complete Flow
```bash
curl -X POST "http://localhost:7071/api/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*PO-TEST-001**20240115~N1*BY*Test Corp*92*TEST-001~PO1*001*5*EA*99.99*PE*VP*PROD-001~CTT*1*5~SE*6*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }'
```

## Using VS Code

### Open the Workspace

```bash
code "Day 7/Final Project/final-project-logic-app/final-project-logic-app.code-workspace"
```

### Debug with VS Code

1. Open the workspace in VS Code
2. Press `F5` or go to **Run > Start Debugging**
3. Select "Attach to Logic App" configuration
4. The Logic App will start with debugging enabled

### View Workflow Designer

1. Navigate to `FinalProject/workflow.json`
2. Right-click and select **Open in Designer**
3. Make changes visually and save

## Troubleshooting

### Common Issues

#### 1. "Azurite is not running"
```
Error: Unable to connect to storage emulator
```
**Solution:** Start Azurite before running the Logic App:
```bash
azurite --silent --location /tmp/azurite
```

#### 2. "Port already in use"
```
Error: Address already in use :::7071
```
**Solution:** Use a different port or kill the existing process:
```bash
# Use different port
func start --port 7073

# Or kill existing process
lsof -ti:7071 | xargs kill -9
```

#### 3. "Cannot find workflow"
```
Error: Workflow 'FinalProject' not found
```
**Solution:** Ensure the workflow folder structure is correct:
- `FinalProject/workflow.json` must exist
- `workflow.json` must have valid JSON

#### 4. "Function URL not reachable"
```
Error: Failed to call function at http://localhost:7072
```
**Solution:**
- Ensure the Azure Function is running on the correct port
- Check `local.settings.json` has the correct `functionAppUrl`

### Viewing Logs

```bash
# View Logic App logs in real-time
func start --verbose

# Or check the Azurite logs
cat /tmp/azurite/debug.log
```

## Workflow Development Tips

### 1. Modify the Workflow

Edit `FinalProject/workflow.json` directly or use the VS Code designer.

### 2. Add a New Workflow

Create a new folder with a `workflow.json` file:

```bash
mkdir NewWorkflow
cat > NewWorkflow/workflow.json << 'EOF'
{
  "definition": {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "contentVersion": "1.0.0.0",
    "triggers": {
      "manual": {
        "type": "Request",
        "kind": "Http",
        "inputs": {
          "method": "POST",
          "schema": {}
        }
      }
    },
    "actions": {},
    "outputs": {}
  },
  "kind": "Stateful"
}
EOF
```

### 3. Stateful vs Stateless Workflows

- **Stateful** (`"kind": "Stateful"`): Persists run history, supports retries
- **Stateless** (`"kind": "Stateless"`): Faster, no history, good for high-throughput

## Deploying to Azure

Once tested locally, deploy to Azure:

```bash
# Option 1: Using deploy script
cd "Day 7/Final Project"
./deploy.sh

# Option 2: Deploy only the Logic App (if infrastructure exists)
cd "Day 7/Final Project/final-project-logic-app/final-project-logic-app"
func azure functionapp publish <LOGIC_APP_NAME>
```

See the main README for full deployment instructions.
