# GitHub Workflow Guide

This guide explains how the CI/CD pipeline works for deploying the X12 850 Order Processing System to Azure.

## Overview

The workflow is defined in `.github/workflows/deploy-azure.yml` and automates:

1. **Build & Test** - Validates code and creates artifacts
2. **Infrastructure Deployment** - Creates Azure resources
3. **Function App Deployment** - Deploys the Python Azure Function
4. **Logic App Deployment** - Deploys the Standard Logic App workflows
5. **Summary** - Reports deployment status

## Workflow Triggers

The pipeline runs automatically on:

```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'Day 7/Final Project/**'
  pull_request:
    branches:
      - main
    paths:
      - 'Day 7/Final Project/**'
  workflow_dispatch:  # Manual trigger
```

| Trigger | When | What Happens |
|---------|------|--------------|
| Push to `main` | Code merged to main branch | Full deployment |
| Pull Request | PR opened/updated against main | Build & test only (no deploy) |
| Manual | Click "Run workflow" in GitHub | Full deployment with options |

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Actions                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐                                                       │
│  │  build-and-test  │  ← Runs on every push/PR                             │
│  │                  │                                                       │
│  │  • Lint Python   │                                                       │
│  │  • Validate JSON │                                                       │
│  │  • Upload        │                                                       │
│  │    artifacts     │                                                       │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           │ (only on push to main)                                          │
│           ▼                                                                 │
│  ┌──────────────────────┐                                                   │
│  │ deploy-infrastructure│                                                   │
│  │                      │                                                   │
│  │  • Resource Group    │                                                   │
│  │  • Storage Account   │                                                   │
│  │  • PostgreSQL        │                                                   │
│  │  • Function App      │                                                   │
│  └────────┬─────────────┘                                                   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────────┐                                                   │
│  │  deploy-function-code│                                                   │
│  │                      │                                                   │
│  │  • Download artifact │                                                   │
│  │  • func publish      │                                                   │
│  └────────┬─────────────┘                                                   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────────┐                                                   │
│  │   deploy-logic-app   │                                                   │
│  │                      │                                                   │
│  │  • Create App Plan   │                                                   │
│  │  • Create Logic App  │                                                   │
│  │  • Deploy workflows  │                                                   │
│  └────────┬─────────────┘                                                   │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────────┐                                                   │
│  │  deployment-summary  │                                                   │
│  │                      │                                                   │
│  │  • Print URLs        │                                                   │
│  │  • GitHub Summary    │                                                   │
│  └──────────────────────┘                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Job Details

### 1. Build and Test (`build-and-test`)

**Purpose:** Validate code quality and prepare deployment artifacts.

**Steps:**
1. Checkout repository
2. Set up Python 3.11
3. Install dependencies
4. Run flake8 linter
5. Validate Logic App workflow.json
6. Upload Function App artifact
7. Upload Logic App artifact

**Artifacts Created:**
- `function-app` - Python Function App code
- `logic-app` - Logic App workflow definitions

### 2. Deploy Infrastructure (`deploy-infrastructure`)

**Purpose:** Create all Azure resources needed for the application.

**Runs:** Only on push to main (not on PRs)

**Resources Created:**

| Resource | Naming Pattern | Purpose |
|----------|---------------|---------|
| Resource Group | `rg-order-processing-{env}` | Container for all resources |
| Storage Account | `orderproc{env}{random}` | Blob storage for mappings |
| PostgreSQL Server | `order-db-{env}-{random}` | Database for orders |
| Function App | `order-func-{env}-{random}` | Hosts Python functions |

**Outputs:**
- `resource_group` - Resource group name
- `storage_account` - Storage account name
- `postgres_host` - PostgreSQL hostname
- `function_app` - Function App name
- `function_url` - Function endpoint URL
- `logic_app` - Logic App name

### 3. Deploy Function Code (`deploy-function-code`)

**Purpose:** Deploy the Python Azure Function code.

**Steps:**
1. Download function-app artifact
2. Azure Login
3. Install Azure Functions Core Tools
4. Run `func azure functionapp publish`

### 4. Deploy Logic App (`deploy-logic-app`)

**Purpose:** Create and deploy the Standard Logic App.

**Steps:**
1. Download logic-app artifact
2. Azure Login
3. Create App Service Plan (WS1 SKU)
4. Create Logic App (Standard)
5. Configure app settings
6. Deploy workflows using `func azure functionapp publish`
7. Get callback URL for HTTP trigger

**App Settings Configured:**
```
AzureWebJobsStorage     = <storage-connection-string>
FUNCTIONS_EXTENSION_VERSION = ~4
FUNCTIONS_WORKER_RUNTIME = dotnet
APP_KIND                = workflowapp
functionAppUrl          = <function-app-url>
```

### 5. Deployment Summary (`deployment-summary`)

**Purpose:** Report deployment results.

**Outputs:**
- Console summary with all resource URLs
- GitHub Actions job summary (visible in Actions tab)

## Environment Variables

### Workflow-level Variables

```yaml
env:
  AZURE_FUNCTIONAPP_PACKAGE_PATH: 'Day 7/Final Project/order-processing-function'
  LOGIC_APP_PACKAGE_PATH: 'Day 7/Final Project/final-project-logic-app/final-project-logic-app'
  PYTHON_VERSION: '3.11'
  DOTNET_VERSION: '8.0.x'
  RESOURCE_GROUP: 'rg-order-processing'
  LOCATION: 'uksouth'
  MAPPING_CONTAINER: 'x12-mappings'
  ORDER_CONTAINER: 'order-documents'
```

## Required GitHub Secrets

Configure these in **Settings > Secrets and variables > Actions**:

| Secret | Description | How to Get |
|--------|-------------|------------|
| `AZURE_CREDENTIALS` | Service Principal JSON | See below |
| `POSTGRES_PASSWORD` | PostgreSQL admin password | Create a secure password |

### Creating AZURE_CREDENTIALS

```bash
# Create Service Principal
az ad sp create-for-rbac \
  --name "github-actions-order-processing" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth

# Output (copy entire JSON to GitHub Secret):
{
  "clientId": "xxx",
  "clientSecret": "xxx",
  "subscriptionId": "xxx",
  "tenantId": "xxx",
  ...
}
```

## Manual Deployment Options

When triggering manually via **Actions > Deploy Order Processing System > Run workflow**:

| Option | Description | Default |
|--------|-------------|---------|
| `environment` | Target environment (dev/staging/prod) | dev |
| `skip_postgres` | Skip PostgreSQL deployment | false |
| `skip_function` | Skip Function App deployment | false |

## Deployment Environments

The workflow supports three environments:

| Environment | Resource Group | Use Case |
|-------------|---------------|----------|
| `dev` | `rg-order-processing-dev` | Development/testing |
| `staging` | `rg-order-processing-staging` | Pre-production |
| `prod` | `rg-order-processing-prod` | Production |

## Workflow Files

```
.github/
└── workflows/
    ├── deploy-azure.yml    # Main deployment workflow
    └── cleanup-azure.yml   # Resource cleanup workflow
```

## Cleanup Workflow

A separate workflow exists for cleaning up resources:

**File:** `.github/workflows/cleanup-azure.yml`

**Trigger:** Manual only (workflow_dispatch)

**Usage:**
1. Go to Actions > Cleanup Azure Resources
2. Click "Run workflow"
3. Select environment (dev/staging/prod)
4. Type "DELETE" to confirm
5. Click "Run workflow"

## Common Scenarios

### Scenario 1: Making Code Changes

```bash
# 1. Create feature branch
git checkout -b feature/my-change

# 2. Make changes to code
# Edit files in Day 7/Final Project/

# 3. Commit and push
git add .
git commit -m "Add my feature"
git push origin feature/my-change

# 4. Create Pull Request
# → Triggers build-and-test job (no deployment)

# 5. Merge to main
# → Triggers full deployment
```

### Scenario 2: Deploy to Specific Environment

1. Go to **Actions** tab
2. Select **Deploy Order Processing System**
3. Click **Run workflow**
4. Choose environment: `staging` or `prod`
5. Click **Run workflow**

### Scenario 3: Redeploy Only Logic App

If you only changed the Logic App workflow:

```bash
# Deploy directly using Azure CLI
cd "Day 7/Final Project/final-project-logic-app/final-project-logic-app"
func azure functionapp publish order-logic-dev
```

### Scenario 4: Skip Database Creation

When database already exists:

1. Go to **Actions** > **Deploy Order Processing System**
2. Click **Run workflow**
3. Check **Skip PostgreSQL deployment**
4. Click **Run workflow**

## Troubleshooting

### Build Fails on Lint

```
Error: flake8 found issues
```

**Solution:** Fix Python code style issues:
```bash
cd "Day 7/Final Project/order-processing-function"
pip install flake8
flake8 . --show-source
# Fix reported issues
```

### Infrastructure Deployment Fails

```
Error: The subscription is not registered to use namespace 'Microsoft.Logic'
```

**Solution:** Register the provider:
```bash
az provider register --namespace Microsoft.Logic
az provider register --namespace Microsoft.Web
```

### Logic App Deployment Fails

```
Error: Workflow 'FinalProject' not found
```

**Solution:** Ensure workflow structure is correct:
```
final-project-logic-app/
└── final-project-logic-app/
    ├── FinalProject/
    │   └── workflow.json    # Must exist
    ├── host.json
    └── local.settings.json
```

### Callback URL Not Available

The callback URL may not be immediately available after deployment.

**Solution:** Get it from Azure Portal:
1. Go to Logic App resource
2. Click **Workflows** > **FinalProject**
3. Click **Overview**
4. Copy the **Workflow URL**

## Monitoring Deployments

### GitHub Actions UI

1. Go to repository **Actions** tab
2. Click on workflow run
3. View job logs and status

### Azure Portal

After deployment, verify resources in Azure Portal:
1. Go to Resource Groups
2. Select `rg-order-processing-{env}`
3. Verify all resources are created

### CLI Verification

```bash
# List resources in group
az resource list \
  --resource-group rg-order-processing-dev \
  --output table

# Check Logic App status
az logicapp show \
  --name order-logic-dev \
  --resource-group rg-order-processing-dev \
  --query "state"

# Check Function App status
az functionapp show \
  --name order-func-dev-xxx \
  --resource-group rg-order-processing-dev \
  --query "state"
```
