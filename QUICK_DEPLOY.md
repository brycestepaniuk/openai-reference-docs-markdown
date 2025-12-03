# Quick Deployment Guide

## Prerequisites
- Azure CLI installed and logged in: `az login`
- Existing App Service Plan (Linux, Python 3.11)

## Quick Steps

1. **Edit `azure-deploy.sh`** with your values:
   ```bash
   RESOURCE_GROUP="your-resource-group"
   APP_SERVICE_PLAN="your-app-service-plan"
   APP_NAME="openai-docs-mcp-server"
   ```

2. **Run the deployment script:**
   ```bash
   ./azure-deploy.sh
   ```

3. **Create deployment package:**
   ```bash
   cd openai-reference-docs-markdown
   zip -r ../deploy.zip . \
     -x '*.git*' '*node_modules*' '*__pycache__*' '*.pyc' '*downloaded_files*'
   ```

4. **Deploy:**
   ```bash
   az webapp deployment source config-zip \
     --name openai-docs-mcp-server \
     --resource-group your-resource-group \
     --src ../deploy.zip
   ```

5. **Check logs:**
   ```bash
   az webapp log tail --name openai-docs-mcp-server --resource-group your-resource-group
   ```

## Important Files
- `app.py` - Main entry point for Azure
- `startup.sh` - Startup script for Linux App Service
- `requirements-app.txt` - Python dependencies
- `.deployment` - Azure deployment configuration

## Verify
Visit: `https://openai-docs-mcp-server.azurewebsites.net`

For detailed instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

