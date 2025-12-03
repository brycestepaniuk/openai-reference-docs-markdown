#!/bin/bash

# Azure App Service Deployment Script
# This script helps deploy the MCP server to Azure App Service

set -e

# Configuration - Update these values
RESOURCE_GROUP="${RESOURCE_GROUP:-your-resource-group}"
APP_SERVICE_PLAN="${APP_SERVICE_PLAN:-your-app-service-plan}"
APP_NAME="${APP_NAME:-openai-docs-mcp-server}"
LOCATION="${LOCATION:-eastus}"

echo "Deploying MCP server to Azure App Service..."
echo "Resource Group: $RESOURCE_GROUP"
echo "App Service Plan: $APP_SERVICE_PLAN"
echo "App Name: $APP_NAME"
echo "Location: $LOCATION"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed. Please install it from https://aka.ms/InstallAzureCLI"
    exit 1
fi

# Login check
echo "Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Using subscription: $SUBSCRIPTION_ID"
echo ""

# Create resource group if it doesn't exist
echo "Creating/verifying resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" || true

# Create or use existing App Service Plan
echo "Checking App Service Plan..."
if ! az appservice plan show --name "$APP_SERVICE_PLAN" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    echo "App Service Plan not found. Please create it first or update the script with the correct name."
    exit 1
fi

# Create Web App (if it doesn't exist)
echo "Creating/updating Web App..."
if ! az webapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    echo "Creating new Web App..."
    az webapp create \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --plan "$APP_SERVICE_PLAN" \
        --runtime "PYTHON:3.11"
else
    echo "Web App already exists. Updating configuration..."
    az webapp config set \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --linux-fx-version "PYTHON|3.11"
fi

# Configure startup command
echo "Configuring startup command..."
az webapp config set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --startup-file "startup.sh"

# Set Python version
echo "Setting Python version..."
az webapp config appsettings set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        ENABLE_ORYX_BUILD=true \
        PYTHON_VERSION=3.11

# Deploy the application
echo "Deploying application files..."
echo "You can deploy using:"
echo "  az webapp deployment source config-zip --name $APP_NAME --resource-group $RESOURCE_GROUP --src <zip-file>"
echo ""
echo "Or use Azure DevOps, GitHub Actions, or VS Code Azure extension"
echo ""
echo "To create a deployment zip:"
echo "  cd openai-reference-docs-markdown"
echo "  zip -r ../deploy.zip . -x '*.git*' -x '*node_modules*' -x '*__pycache__*' -x '*.pyc'"
echo ""
echo "Then deploy with:"
echo "  az webapp deployment source config-zip --name $APP_NAME --resource-group $RESOURCE_GROUP --src ../deploy.zip"

