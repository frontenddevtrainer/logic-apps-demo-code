#!/bin/bash
set -e

echo ">>> Starting full VNET + PostgreSQL + Logic App Standard setup in UK South..."

# ---------------------------------------------------------
# VARIABLES
# ---------------------------------------------------------
RG="rg-app-uksouth-demo"
LOCATION="uksouth"

VNET_NAME="vnet-core-demo"
SUBNET_APP="snet-app-demo"
SUBNET_DB="snet-postgres-demo"

POSTGRES_NAME="pgflexuks01-demo"
POSTGRES_ADMIN="pgadmin01-demo"
POSTGRES_PASSWORD="PgStrongPass123!"

DNS_ZONE="privatelink.postgres.database.azure.com"

PLAN_NAME="asp-la-uks01"
LA_NAME="la-std-uks01"

SA_NAME="stgla$(date +%s)"   # Unique storage name

# ---------------------------------------------------------
# RESOURCE GROUP
# ---------------------------------------------------------
echo ">>> Creating resource group..."
az group create -n $RG -l $LOCATION

# ---------------------------------------------------------
# VNET & SUBNETS
# ---------------------------------------------------------
echo ">>> Creating VNET and subnets..."
az network vnet create \
  -g $RG -n $VNET_NAME \
  --address-prefix 10.20.0.0/16 \
  --subnet-name $SUBNET_APP \
  --subnet-prefix 10.20.2.0/24

az network vnet subnet create \
  -g $RG --vnet-name $VNET_NAME \
  -n $SUBNET_DB \
  --address-prefixes 10.20.1.0/24

# ---------------------------------------------------------
# PRIVATE DNS ZONE
# ---------------------------------------------------------
echo ">>> Creating Private DNS zone for PostgreSQL..."
az network private-dns zone create \
  -g $RG -n $DNS_ZONE

echo ">>> Linking DNS zone to VNET..."
az network private-dns link vnet create \
  -g $RG \
  -n pgdnslink \
  -z $DNS_ZONE \
  -v $VNET_NAME \
  --registration-enabled false

# ---------------------------------------------------------
# DELEGATE POSTGRES SUBNET
# ---------------------------------------------------------
echo ">>> Delegating subnet for PostgreSQL Flexible Server..."
az network vnet subnet update \
  -g $RG --vnet-name $VNET_NAME \
  -n $SUBNET_DB \
  --delegations Microsoft.DBforPostgreSQL/flexibleServers

# ---------------------------------------------------------
# DEPLOY POSTGRESQL FLEX SERVER
# ---------------------------------------------------------
echo ">>> Creating PostgreSQL Flexible Server in Private VNET mode..."
az postgres flexible-server create \
  --name $POSTGRES_NAME \
  --resource-group $RG \
  --location $LOCATION \
  --admin-user $POSTGRES_ADMIN \
  --admin-password "$POSTGRES_PASSWORD" \
  --vnet $VNET_NAME \
  --subnet $SUBNET_DB \
  --private-dns-zone $DNS_ZONE \
  --yes

# ---------------------------------------------------------
# CREATE NSG + RULES
# ---------------------------------------------------------
echo ">>> Creating NSG and allowing App Subnet to reach PostgreSQL..."
az network nsg create -g $RG -n nsg-postgres

az network vnet subnet update \
  -g $RG --vnet-name $VNET_NAME \
  -n $SUBNET_DB \
  --network-security-group nsg-postgres

az network nsg rule create \
  -g $RG \
  --nsg-name nsg-postgres \
  --name Allow-App-To-Postgres \
  --priority 100 \
  --source-address-prefixes 10.20.2.0/24 \
  --destination-port-ranges 5432 \
  --protocol Tcp \
  --access Allow

# ---------------------------------------------------------
# STORAGE ACCOUNT
# ---------------------------------------------------------
echo ">>> Creating storage account: $SA_NAME"
az storage account create \
  --name $SA_NAME \
  --resource-group $RG \
  --location $LOCATION \
  --sku Standard_LRS

# ---------------------------------------------------------
# APP SERVICE PLAN
# ---------------------------------------------------------
echo ">>> Creating App Service Plan for Logic App Standard..."
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RG \
  --location $LOCATION \
  --sku WS1 \
  --is-linux

# ---------------------------------------------------------
# LOGIC APP STANDARD
# ---------------------------------------------------------
echo ">>> Creating Logic App Standard (Web App hosting Logic Apps runtime)..."

az webapp create \
  --resource-group $RG \
  --plan $PLAN_NAME \
  --name $LA_NAME \
  --runtime "dotnet" \
  --deployment-container-image-name "mcr.microsoft.com/azure-functions/dotnet:4"

echo ">>> Logic App Standard Web App created."

# ---------------------------------------------------------
# ENABLE VNET INTEGRATION
# ---------------------------------------------------------
echo ">>> Enabling VNET Integration for Logic App..."
az webapp vnet-integration add \
  --resource-group $RG \
  --name $LA_NAME \
  --vnet $VNET_NAME \
  --subnet $SUBNET_APP

# ---------------------------------------------------------
# OUTPUT DETAILS
# ---------------------------------------------------------
echo ">>> Setup completed!"
echo "PostgreSQL Private Hostname:"
az postgres flexible-server show \
  -g $RG -n $POSTGRES_NAME \
  --query "fullyQualifiedDomainName" -o tsv

echo "Resource Group: $RG"
echo "Logic App Standard: $LA_NAME"
echo "PostgreSQL: $POSTGRES_NAME"
echo "VNET: $VNET_NAME"
echo "Subnets: $SUBNET_APP, $SUBNET_DB"
echo "DNS Zone: $DNS_ZONE"

echo ">>> All resources deployed successfully in UK South!"
