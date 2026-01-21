# Debugging Guide: Function App & Logic App

This guide covers debugging techniques for the X12 850 Order Processing system, including local debugging, Azure debugging, and viewing execution history.

## Table of Contents

1. [Local Debugging](#local-debugging)
   - [Function App Debugging](#function-app-debugging)
   - [Logic App Debugging](#logic-app-debugging)
2. [Azure Debugging](#azure-debugging)
   - [Function App Logs](#function-app-logs-in-azure)
   - [Logic App Execution History](#logic-app-execution-history)
3. [X12 Message Debugging](#x12-message-debugging)
4. [Common Issues & Solutions](#common-issues--solutions)

---

## Local Debugging

### Function App Debugging

#### 1. Setup VS Code for Debugging

Create/update `.vscode/launch.json` in the function app folder:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to Python Functions",
      "type": "python",
      "request": "attach",
      "port": 9091,
      "preLaunchTask": "func: host start"
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

#### 2. Start Function App with Debugging

```bash
cd "Day 7/Final Project/order-processing-function"

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start with verbose logging
func start --verbose --python

# Or start with specific log level
func start --python --verbose --debug
```

#### 3. Add Breakpoints and Debug

Add logging statements to your function code:

```python
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('=== Starting X12 Processing ===')

    # Log the incoming request
    body = req.get_json()
    logging.debug(f'Request body: {body}')

    x12_data = body.get('x12', '')
    logging.info(f'X12 data length: {len(x12_data)}')

    # Add debug breakpoint
    import pdb; pdb.set_trace()  # Debugger will pause here

    # Continue processing...
```

#### 4. Test with curl

```bash
# Basic test
curl -X POST "http://localhost:7072/api/process-order" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*PO-TEST-001**20240115~N1*BY*Test Corp*92*TEST-001~PO1*001*5*EA*99.99*PE*VP*PROD-001~CTT*1*5~SE*6*0001~GE*1*1~IEA*1*000000001~",
    "transactionSet": "850"
  }' | jq .

# Save response to file for analysis
curl -X POST "http://localhost:7072/api/process-order" \
  -H "Content-Type: application/json" \
  -d @test-order.json \
  -o response.json

# Verbose output with headers
curl -v -X POST "http://localhost:7072/api/process-order" \
  -H "Content-Type: application/json" \
  -d @test-order.json
```

#### 5. View Real-time Logs

```bash
# Terminal 1: Start function with streaming logs
func start --python 2>&1 | tee function-logs.txt

# Terminal 2: Follow the log file
tail -f function-logs.txt | grep -E "(ERROR|WARNING|INFO|X12)"
```

### Logic App Debugging

#### 1. Start Logic App Locally

```bash
cd "Day 7/Final Project/final-project-logic-app/final-project-logic-app"

# Start with verbose output
func start --verbose --port 7071
```

#### 2. View Workflow Run History (Local)

When running locally, workflow runs are stored in Azurite. View them using Azure Storage Explorer:

1. Open Azure Storage Explorer
2. Connect to **Local & Attached > Storage Accounts > Emulator**
3. Navigate to **Blob Containers > azure-webjobs-hosts**
4. Find workflow run data in the container

#### 3. Debug Workflow Definitions

Check workflow.json syntax:

```bash
# Validate JSON syntax
python -c "import json; json.load(open('FinalProject/workflow.json'))"

# Pretty print for review
cat FinalProject/workflow.json | jq .
```

#### 4. Test Logic App Endpoint

```bash
# Get the local trigger URL (shown when func start runs)
# Usually: http://localhost:7071/api/FinalProject/triggers/{trigger-name}/invoke

curl -X POST "http://localhost:7071/api/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "x12": "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~",
    "transactionSet": "850"
  }'
```

---

## Azure Debugging

### Function App Logs in Azure

#### 1. View Logs via Azure Portal

1. Go to **Azure Portal** > **Function App**
2. Select your function (e.g., `order-func-dev-xxx`)
3. Click **Functions** > **process-order**
4. Click **Monitor** to see invocation logs
5. Click on any invocation to see details

#### 2. Live Log Streaming (Portal)

1. Go to Function App > **Log stream**
2. Watch real-time logs as requests come in
3. Filter by log level if needed

#### 3. View Logs via Azure CLI

```bash
# Stream live logs
az webapp log tail \
  --name order-func-dev-xxx \
  --resource-group rg-order-processing-dev

# Download logs
az webapp log download \
  --name order-func-dev-xxx \
  --resource-group rg-order-processing-dev \
  --log-file logs.zip

# View recent logs
az functionapp log deployment list \
  --name order-func-dev-xxx \
  --resource-group rg-order-processing-dev
```

#### 4. Application Insights Queries

If Application Insights is enabled:

1. Go to **Application Insights** resource
2. Click **Logs**
3. Run queries:

```kusto
// View all function invocations
requests
| where cloud_RoleName == "order-func-dev-xxx"
| order by timestamp desc
| take 100

// View errors only
exceptions
| where cloud_RoleName == "order-func-dev-xxx"
| order by timestamp desc
| take 50

// View X12 processing traces
traces
| where message contains "X12" or message contains "850"
| order by timestamp desc
| take 100

// Function execution duration
requests
| where cloud_RoleName == "order-func-dev-xxx"
| summarize avg(duration), max(duration), min(duration) by bin(timestamp, 1h)
| render timechart

// Failed requests with details
requests
| where success == false
| project timestamp, name, resultCode, duration, operation_Id
| order by timestamp desc
```

#### 5. Enable Detailed Logging

Update Function App settings:

```bash
az functionapp config appsettings set \
  --name order-func-dev-xxx \
  --resource-group rg-order-processing-dev \
  --settings \
    "AzureFunctionsJobHost__logging__logLevel__default=Debug" \
    "AzureFunctionsJobHost__logging__logLevel__Function=Debug"
```

### Logic App Execution History

#### 1. View Run History (Portal)

1. Go to **Azure Portal** > **Logic App**
2. Select your Logic App (e.g., `order-logic-dev`)
3. Click **Workflows** > **FinalProject**
4. Click **Run History** (or **Overview** > **Runs**)
5. Click on any run to see details

#### 2. Analyze Individual Runs

For each run, you can see:

- **Status**: Succeeded, Failed, Running, Cancelled
- **Start/End Time**: Duration of execution
- **Trigger**: What started the workflow
- **Actions**: Each step with input/output

Click on any action to see:
- **Inputs**: What data went into the action
- **Outputs**: What the action returned
- **Duration**: How long it took
- **Error**: If failed, the error message

#### 3. View Runs via Azure CLI

```bash
# List workflow runs
az rest --method GET \
  --uri "https://management.azure.com/subscriptions/{sub-id}/resourceGroups/rg-order-processing-dev/providers/Microsoft.Web/sites/order-logic-dev/hostruntime/runtime/webhooks/workflow/api/management/workflows/FinalProject/runs?api-version=2022-03-01" \
  | jq '.value[] | {name: .name, status: .properties.status, startTime: .properties.startTime}'

# Get specific run details
az rest --method GET \
  --uri "https://management.azure.com/subscriptions/{sub-id}/resourceGroups/rg-order-processing-dev/providers/Microsoft.Web/sites/order-logic-dev/hostruntime/runtime/webhooks/workflow/api/management/workflows/FinalProject/runs/{run-id}?api-version=2022-03-01" \
  | jq .
```

#### 4. Resubmit Failed Runs

1. Go to Logic App > Workflows > FinalProject > Run History
2. Find the failed run
3. Click **Resubmit** to retry with same inputs

#### 5. Enable Diagnostic Logging

```bash
# Enable diagnostic settings
az monitor diagnostic-settings create \
  --name "logic-app-diagnostics" \
  --resource "/subscriptions/{sub-id}/resourceGroups/rg-order-processing-dev/providers/Microsoft.Web/sites/order-logic-dev" \
  --logs '[{"category": "WorkflowRuntime", "enabled": true}]' \
  --workspace "/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.OperationalInsights/workspaces/{workspace}"
```

---

## X12 Message Debugging

### 1. Parse and Validate X12 Locally

Create a debug script `debug-x12.py`:

```python
#!/usr/bin/env python3
"""Debug script for X12 message parsing."""

import json
import sys

def parse_x12(x12_string: str) -> dict:
    """Parse X12 message into segments."""
    # Detect segment terminator
    terminator = '~'
    if '~' not in x12_string and '\n' in x12_string:
        terminator = '\n'

    segments = [s.strip() for s in x12_string.split(terminator) if s.strip()]

    parsed = {
        'segment_count': len(segments),
        'segments': []
    }

    for seg in segments:
        elements = seg.split('*')
        segment_id = elements[0]
        parsed['segments'].append({
            'id': segment_id,
            'elements': elements,
            'raw': seg
        })

    return parsed

def analyze_850(parsed: dict) -> dict:
    """Analyze 850 Purchase Order segments."""
    analysis = {
        'transaction_set': None,
        'purchase_order': None,
        'buyer': None,
        'line_items': [],
        'errors': []
    }

    for seg in parsed['segments']:
        seg_id = seg['id']
        elements = seg['elements']

        if seg_id == 'ST':
            if len(elements) >= 2:
                analysis['transaction_set'] = {
                    'code': elements[1],
                    'control_number': elements[2] if len(elements) > 2 else None
                }
                if elements[1] != '850':
                    analysis['errors'].append(f"Expected 850, got {elements[1]}")

        elif seg_id == 'BEG':
            if len(elements) >= 4:
                analysis['purchase_order'] = {
                    'purpose_code': elements[1],
                    'type_code': elements[2],
                    'po_number': elements[3],
                    'date': elements[5] if len(elements) > 5 else None
                }

        elif seg_id == 'N1':
            if len(elements) >= 3:
                entity = {
                    'entity_code': elements[1],
                    'name': elements[2],
                    'id_qualifier': elements[3] if len(elements) > 3 else None,
                    'id': elements[4] if len(elements) > 4 else None
                }
                if elements[1] == 'BY':
                    analysis['buyer'] = entity

        elif seg_id == 'PO1':
            if len(elements) >= 5:
                analysis['line_items'].append({
                    'line_number': elements[1],
                    'quantity': elements[2],
                    'unit': elements[3],
                    'unit_price': elements[4],
                    'product_id': elements[7] if len(elements) > 7 else None
                })

    return analysis

def main():
    # Test X12 message
    test_x12 = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~
GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~
ST*850*0001~
BEG*00*SA*PO-TEST-001**20240115~
N1*BY*Test Corp*92*TEST-001~
PO1*001*5*EA*99.99*PE*VP*PROD-001~
PO1*002*10*EA*49.99*PE*VP*PROD-002~
CTT*2*15~
SE*7*0001~
GE*1*1~
IEA*1*000000001~"""

    if len(sys.argv) > 1:
        # Read from file
        with open(sys.argv[1], 'r') as f:
            test_x12 = f.read()

    print("=" * 60)
    print("X12 MESSAGE DEBUGGER")
    print("=" * 60)

    # Parse
    parsed = parse_x12(test_x12)
    print(f"\nTotal Segments: {parsed['segment_count']}")
    print("\nSegments:")
    for seg in parsed['segments']:
        print(f"  {seg['id']}: {seg['raw'][:60]}{'...' if len(seg['raw']) > 60 else ''}")

    # Analyze 850
    analysis = analyze_850(parsed)
    print("\n" + "=" * 60)
    print("850 ANALYSIS")
    print("=" * 60)
    print(json.dumps(analysis, indent=2))

    # Check for errors
    if analysis['errors']:
        print("\nERRORS FOUND:")
        for err in analysis['errors']:
            print(f"  - {err}")

    return analysis

if __name__ == '__main__':
    main()
```

Run the debug script:

```bash
# Debug inline X12
python debug-x12.py

# Debug from file
python debug-x12.py sample-order.x12
```

### 2. X12 Segment Reference

Common 850 segments to check:

| Segment | Description | Example |
|---------|-------------|---------|
| ISA | Interchange Control Header | `ISA*00*...*~` |
| GS | Functional Group Header | `GS*PO*SENDER*RECEIVER*...~` |
| ST | Transaction Set Header | `ST*850*0001~` |
| BEG | Beginning Segment | `BEG*00*SA*PO-001**20240115~` |
| N1 | Name/Party | `N1*BY*Company Name*92*ID~` |
| PO1 | Line Item | `PO1*1*5*EA*99.99*PE*VP*SKU~` |
| CTT | Transaction Totals | `CTT*2*15~` |
| SE | Transaction Set Trailer | `SE*7*0001~` |
| GE | Functional Group Trailer | `GE*1*1~` |
| IEA | Interchange Control Trailer | `IEA*1*000000001~` |

### 3. Common X12 Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid segment terminator" | Missing or wrong `~` | Ensure each segment ends with `~` |
| "Missing ISA segment" | No interchange header | Add ISA segment at start |
| "Segment count mismatch" | SE count != actual | Update SE segment count |
| "Control number mismatch" | ST/SE numbers differ | Match control numbers |
| "Invalid element separator" | Wrong `*` character | Use standard `*` separator |

---

## Common Issues & Solutions

### Function App Issues

#### Issue: Function returns 500 error

**Debug steps:**
```bash
# 1. Check function logs
az webapp log tail --name order-func-dev-xxx --resource-group rg-order-processing-dev

# 2. Test locally first
func start --python --verbose

# 3. Check app settings
az functionapp config appsettings list \
  --name order-func-dev-xxx \
  --resource-group rg-order-processing-dev
```

#### Issue: Function timeout

**Solution:**
```bash
# Increase timeout (default 5 min, max 10 min for consumption)
az functionapp config appsettings set \
  --name order-func-dev-xxx \
  --resource-group rg-order-processing-dev \
  --settings "AzureFunctionsJobHost__functionTimeout=00:10:00"
```

#### Issue: Missing dependencies

**Debug:**
```bash
# Check requirements.txt is deployed
func azure functionapp publish order-func-dev-xxx --python --build remote

# Or build locally
pip install -r requirements.txt -t .python_packages/lib/site-packages
```

### Logic App Issues

#### Issue: Workflow not found

**Debug:**
```bash
# Check workflow structure
ls -la FinalProject/
cat FinalProject/workflow.json | jq .definition.triggers

# Redeploy
func azure functionapp publish order-logic-dev
```

#### Issue: HTTP action fails

**Check in Portal:**
1. Go to Run History > Failed Run
2. Click on the HTTP action
3. View **Inputs** (request sent) and **Outputs** (response received)
4. Check error message

**Common fixes:**
- Verify Function App URL in app settings
- Check Function App is running
- Verify network connectivity

#### Issue: Trigger URL not working

**Get correct URL:**
```bash
# Via Azure CLI
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
az rest --method POST \
  --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/rg-order-processing-dev/providers/Microsoft.Web/sites/order-logic-dev/hostruntime/runtime/webhooks/workflow/api/management/workflows/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/listCallbackUrl?api-version=2022-03-01" \
  --query value -o tsv
```

### Database Issues

#### Issue: Cannot connect to PostgreSQL

**Debug:**
```bash
# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group rg-order-processing-dev \
  --name order-db-dev-xxx

# Add your IP temporarily
MY_IP=$(curl -s https://api.ipify.org)
az postgres flexible-server firewall-rule create \
  --resource-group rg-order-processing-dev \
  --name order-db-dev-xxx \
  --rule-name AllowMyIP \
  --start-ip-address "$MY_IP" \
  --end-ip-address "$MY_IP"

# Test connection
psql -h order-db-dev-xxx.postgres.database.azure.com \
  -U orderadmin \
  -d order_processing
```

---

## Quick Reference Commands

```bash
# === Local Debugging ===
# Start Function App
cd "Day 7/Final Project/order-processing-function"
func start --python --verbose

# Start Logic App
cd "Day 7/Final Project/final-project-logic-app/final-project-logic-app"
func start --verbose --port 7071

# === Azure Logs ===
# Stream Function logs
az webapp log tail --name <func-name> --resource-group <rg>

# Stream Logic App logs
az webapp log tail --name <logic-app-name> --resource-group <rg>

# === Application Insights ===
# Open in browser
az monitor app-insights component show \
  --app <app-insights-name> \
  --resource-group <rg> \
  --query "instrumentationKey"

# === Quick Tests ===
# Test Function locally
curl -X POST http://localhost:7072/api/process-order \
  -H "Content-Type: application/json" \
  -d '{"x12": "ISA*...", "transactionSet": "850"}'

# Test Logic App locally
curl -X POST http://localhost:7071/api/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/invoke \
  -H "Content-Type: application/json" \
  -d '{"x12": "ISA*...", "transactionSet": "850"}'
```
