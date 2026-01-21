#!/usr/bin/env bash
#
# Deploy script for Final Project: X12 850 Order Processing System
#
# This script creates all required Azure resources:
# - Resource Group
# - Storage Account (for mappings and order documents)
# - PostgreSQL Flexible Server
# - Azure Function App
# - Logic App (Standard)
#
# Usage:
#   ./deploy.sh                    # Deploy with default settings
#   ./deploy.sh --skip-postgres    # Skip PostgreSQL creation (use existing)
#   ./deploy.sh --skip-function    # Skip Function App deployment
#   ./deploy.sh --skip-logic-app   # Skip Logic App deployment
#   ./deploy.sh --cleanup          # Delete all resources
#
set -euo pipefail

# =============================================================================
# Configuration (can be overridden via environment variables)
# =============================================================================
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-order-processing}"
LOCATION="${LOCATION:-uksouth}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-orderproc$RANDOM}"
POSTGRES_SERVER="${POSTGRES_SERVER:-order-db-$RANDOM}"
POSTGRES_DB="${POSTGRES_DB:-order_processing}"
POSTGRES_USER="${POSTGRES_USER:-orderadmin}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
FUNCTION_APP="${FUNCTION_APP:-order-processing-func-$RANDOM}"
LOGIC_APP="${LOGIC_APP:-order-processing-logic}"
LOGIC_APP_PLAN="${LOGIC_APP_PLAN:-${LOGIC_APP}-plan}"

MAPPING_CONTAINER="x12-mappings"
ORDER_CONTAINER="order-documents"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGIC_APP_PATH="$SCRIPT_DIR/final-project-logic-app/final-project-logic-app"

# =============================================================================
# Helper Functions
# =============================================================================
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
  echo "[ERROR] $*" >&2
  exit 1
}

check_prerequisites() {
  log "Checking prerequisites..."

  if ! command -v az >/dev/null 2>&1; then
    error "Azure CLI (az) is required. Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
  fi

  if ! command -v func >/dev/null 2>&1; then
    error "Azure Functions Core Tools (func) is required. Install from: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local"
  fi

  if ! az account show >/dev/null 2>&1; then
    error "Azure CLI is not logged in. Run: az login"
  fi

  log "Prerequisites check passed."
}

generate_password() {
  # Generate a secure password if not provided
  if [[ -z "$POSTGRES_PASSWORD" ]]; then
    POSTGRES_PASSWORD="$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)@1Aa"
    log "Generated PostgreSQL password (save this): $POSTGRES_PASSWORD"
  fi
}

# =============================================================================
# Cleanup Function
# =============================================================================
cleanup() {
  log "Deleting resource group: $RESOURCE_GROUP"
  az group delete --name "$RESOURCE_GROUP" --yes --no-wait
  log "Resource group deletion initiated. This may take a few minutes."
  exit 0
}

# =============================================================================
# Resource Creation Functions
# =============================================================================
create_resource_group() {
  log "Creating resource group: $RESOURCE_GROUP in $LOCATION"
  az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none
}

create_storage_account() {
  log "Creating storage account: $STORAGE_ACCOUNT"
  az storage account create \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --output none

  log "Creating blob containers..."
  STORAGE_CONN=$(az storage account show-connection-string \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

  az storage container create \
    --name "$MAPPING_CONTAINER" \
    --connection-string "$STORAGE_CONN" \
    --output none

  az storage container create \
    --name "$ORDER_CONTAINER" \
    --connection-string "$STORAGE_CONN" \
    --output none

  log "Uploading X12 850 mapping file..."
  az storage blob upload \
    --container-name "$MAPPING_CONTAINER" \
    --name "mapping/standards/850.json" \
    --file "$SCRIPT_DIR/mappings/standards/850.json" \
    --connection-string "$STORAGE_CONN" \
    --overwrite \
    --output none
}

create_postgres() {
  log "Creating PostgreSQL Flexible Server: $POSTGRES_SERVER"

  az postgres flexible-server create \
    --name "$POSTGRES_SERVER" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --admin-user "$POSTGRES_USER" \
    --admin-password "$POSTGRES_PASSWORD" \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --storage-size 32 \
    --version 14 \
    --yes \
    --output none

  log "Configuring PostgreSQL firewall (allow Azure services)..."
  az postgres flexible-server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$POSTGRES_SERVER" \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0 \
    --output none

  log "Creating database: $POSTGRES_DB"
  az postgres flexible-server db create \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$POSTGRES_SERVER" \
    --database-name "$POSTGRES_DB" \
    --output none

  log "Running database schema..."
  POSTGRES_HOST="$POSTGRES_SERVER.postgres.database.azure.com"

  # Allow current IP temporarily
  MY_IP=$(curl -s https://api.ipify.org)
  az postgres flexible-server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$POSTGRES_SERVER" \
    --rule-name AllowMyIP \
    --start-ip-address "$MY_IP" \
    --end-ip-address "$MY_IP" \
    --output none 2>/dev/null || true

  PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -f "$SCRIPT_DIR/database/schema.sql" \
    2>/dev/null || log "Note: Could not run schema automatically. Run manually: psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -f database/schema.sql"
}

create_function_app() {
  log "Creating Function App: $FUNCTION_APP"

  az functionapp create \
    --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --consumption-plan-location "$LOCATION" \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --storage-account "$STORAGE_ACCOUNT" \
    --os-type Linux \
    --output none

  POSTGRES_HOST="$POSTGRES_SERVER.postgres.database.azure.com"
  STORAGE_CONN=$(az storage account show-connection-string \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

  log "Configuring Function App settings..."
  az functionapp config appsettings set \
    --name "$FUNCTION_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
      MAPPING_STORAGE_CONNECTION="$STORAGE_CONN" \
      MAPPING_CONTAINER="$MAPPING_CONTAINER" \
      MAPPING_ROOT="mapping" \
      ORDER_STORAGE_CONNECTION="$STORAGE_CONN" \
      ORDER_CONTAINER="$ORDER_CONTAINER" \
      POSTGRES_HOST="$POSTGRES_HOST" \
      POSTGRES_DB="$POSTGRES_DB" \
      POSTGRES_USER="$POSTGRES_USER" \
      POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
      POSTGRES_PORT="5432" \
      POSTGRES_SSLMODE="require" \
    --output none

  log "Deploying Function App code..."
  cd "$SCRIPT_DIR/order-processing-function"
  func azure functionapp publish "$FUNCTION_APP" --python
  cd "$SCRIPT_DIR"
}

create_logic_app() {
  log "Creating Logic App (Standard): $LOGIC_APP"

  FUNCTION_URL="https://$FUNCTION_APP.azurewebsites.net/api/process-order"
  STORAGE_CONN=$(az storage account show-connection-string \
    --name "$STORAGE_ACCOUNT" \
    --resource-group "$RESOURCE_GROUP" \
    --query connectionString -o tsv)

  # Create App Service Plan for Logic App (Workflow Standard WS1)
  log "Creating App Service Plan: $LOGIC_APP_PLAN"
  az appservice plan create \
    --name "$LOGIC_APP_PLAN" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --sku WS1 \
    --is-linux false \
    --output none

  # Create Logic App (Standard)
  log "Creating Logic App (Standard) resource..."
  az logicapp create \
    --name "$LOGIC_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$LOGIC_APP_PLAN" \
    --storage-account "$STORAGE_ACCOUNT" \
    --output none

  # Configure Logic App settings
  log "Configuring Logic App settings..."
  az logicapp config appsettings set \
    --name "$LOGIC_APP" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
      "AzureWebJobsStorage=$STORAGE_CONN" \
      "FUNCTIONS_EXTENSION_VERSION=~4" \
      "FUNCTIONS_WORKER_RUNTIME=dotnet" \
      "APP_KIND=workflowapp" \
      "functionAppUrl=$FUNCTION_URL" \
    --output none

  # Deploy Logic App workflows
  log "Deploying Logic App workflows..."
  cd "$LOGIC_APP_PATH"
  func azure functionapp publish "$LOGIC_APP"
  cd "$SCRIPT_DIR"

  # Wait for deployment to complete
  sleep 10

  log "Getting Logic App callback URL..."
  SUBSCRIPTION_ID=$(az account show --query id -o tsv)
  LOGIC_APP_URL=$(az rest \
    --method POST \
    --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/${LOGIC_APP}/hostruntime/runtime/webhooks/workflow/api/management/workflows/FinalProject/triggers/HTTP_Request_-_Receive_X12_Order/listCallbackUrl?api-version=2022-03-01" \
    --query value -o tsv 2>/dev/null || echo "URL will be available in Azure Portal")
}

print_summary() {
  log "=========================================="
  log "Deployment Complete!"
  log "=========================================="
  echo ""
  echo "Resource Group:    $RESOURCE_GROUP"
  echo "Location:          $LOCATION"
  echo ""
  echo "Storage Account:   $STORAGE_ACCOUNT"
  echo "  - Mapping Container: $MAPPING_CONTAINER"
  echo "  - Order Container:   $ORDER_CONTAINER"
  echo ""
  echo "PostgreSQL Server: $POSTGRES_SERVER.postgres.database.azure.com"
  echo "  - Database:      $POSTGRES_DB"
  echo "  - User:          $POSTGRES_USER"
  echo "  - Password:      $POSTGRES_PASSWORD"
  echo ""
  echo "Function App:      $FUNCTION_APP"
  echo "  - X12 Map:       https://$FUNCTION_APP.azurewebsites.net/api/x12-map"
  echo "  - Process Order: https://$FUNCTION_APP.azurewebsites.net/api/process-order"
  echo ""
  echo "Logic App (Standard): $LOGIC_APP"
  echo "  - Plan:          $LOGIC_APP_PLAN"
  echo "  - Workflow:      FinalProject"
  if [[ -n "${LOGIC_APP_URL:-}" && "$LOGIC_APP_URL" != "URL will be available in Azure Portal" ]]; then
    echo "  - Endpoint:      $LOGIC_APP_URL"
  else
    echo "  - Endpoint:      (Get from Azure Portal > Logic App > Workflows > FinalProject)"
  fi
  echo ""
  echo "=========================================="
  echo "Test Command:"
  echo "=========================================="
  echo ""
  echo "curl -X POST \"https://$FUNCTION_APP.azurewebsites.net/api/process-order\" \\"
  echo "  -H \"Content-Type: application/json\" \\"
  echo "  -d '{"
  echo "    \"x12\": \"ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *240115*1030*U*00401*000000001*0*P*:~GS*PO*SENDER*RECEIVER*20240115*1030*1*X*004010~ST*850*0001~BEG*00*SA*PO-TEST-001**20240115~N1*BY*Test Corp*92*TEST-001~PO1*001*5*EA*99.99*PE*VP*PROD-001~CTT*1*5~SE*6*0001~GE*1*1~IEA*1*000000001~\","
  echo "    \"transactionSet\": \"850\""
  echo "  }'"
  echo ""
}

# =============================================================================
# Main Script
# =============================================================================
SKIP_POSTGRES=false
SKIP_FUNCTION=false
SKIP_LOGIC_APP=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --cleanup)
      cleanup
      ;;
    --skip-postgres)
      SKIP_POSTGRES=true
      shift
      ;;
    --skip-function)
      SKIP_FUNCTION=true
      shift
      ;;
    --skip-logic-app)
      SKIP_LOGIC_APP=true
      shift
      ;;
    *)
      error "Unknown option: $1"
      ;;
  esac
done

check_prerequisites
generate_password

log "Starting deployment..."
log "Resource Group: $RESOURCE_GROUP"
log "Location: $LOCATION"

create_resource_group
create_storage_account

if [[ "$SKIP_POSTGRES" == "false" ]]; then
  create_postgres
else
  log "Skipping PostgreSQL creation (--skip-postgres)"
fi

if [[ "$SKIP_FUNCTION" == "false" ]]; then
  create_function_app
else
  log "Skipping Function App deployment (--skip-function)"
fi

if [[ "$SKIP_LOGIC_APP" == "false" ]]; then
  create_logic_app
else
  log "Skipping Logic App deployment (--skip-logic-app)"
fi

print_summary
