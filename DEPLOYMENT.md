# Azure App Service Deployment Guide

This guide explains how to deploy the OpenAI Documentation MCP Server to Azure App Service on an existing App Service Plan.

## Prerequisites

1. **Azure CLI** installed and configured
   ```bash
   # Install Azure CLI if needed
   # macOS: brew install azure-cli
   # Or download from: https://aka.ms/InstallAzureCLI
   
   # Login to Azure
   az login
   ```

2. **Existing App Service Plan** in your Azure subscription
   - Note the Resource Group name
   - Note the App Service Plan name
   - Ensure it's a Linux plan (Python apps require Linux on Azure App Service)

3. **Python 3.11** (Azure App Service will use this)

## Deployment Steps

### Option 1: Using Azure CLI (Recommended)

1. **Update the deployment script variables:**
   
   Edit `azure-deploy.sh` and set:
   ```bash
   RESOURCE_GROUP="your-resource-group"
   APP_SERVICE_PLAN="your-app-service-plan"
   APP_NAME="openai-docs-mcp-server"  # Choose a unique name
   LOCATION="eastus"  # Match your App Service Plan location
   ```

2. **Make the script executable and run it:**
   ```bash
   chmod +x azure-deploy.sh
   ./azure-deploy.sh
   ```

3. **Create a deployment package:**
   ```bash
   cd openai-reference-docs-markdown
   # Exclude unnecessary files
   zip -r ../deploy.zip . \
     -x '*.git*' \
     -x '*node_modules*' \
     -x '*__pycache__*' \
     -x '*.pyc' \
     -x '*.pyo' \
     -x '*downloaded_files*' \
     -x '*.lock' \
     -x '*.log'
   ```

4. **Deploy the zip file:**
   ```bash
   az webapp deployment source config-zip \
     --name openai-docs-mcp-server \
     --resource-group your-resource-group \
     --src ../deploy.zip
   ```

### Option 2: Using Azure Portal

1. **Create a new Web App:**
   - Go to Azure Portal → Create a resource → Web App
   - Select "Use existing" for App Service Plan
   - Choose your existing App Service Plan
   - Set Runtime stack to "Python 3.11"
   - Create the app

2. **Configure the app:**
   - Go to Configuration → General settings
   - Set Startup Command to: `startup.sh`
   - Save

3. **Deploy code:**
   - Go to Deployment Center
   - Choose your deployment method (GitHub, Azure DevOps, Local Git, or ZIP deploy)
   - Follow the prompts

### Option 3: Using VS Code Azure Extension

1. **Install Azure App Service extension** in VS Code

2. **Right-click on the `openai-reference-docs-markdown` folder**
   - Select "Deploy to Web App..."
   - Choose your subscription and App Service Plan
   - Follow the prompts

## Configuration

### Required App Settings

Set these in Azure Portal → Configuration → Application settings:

- `MCP_TRANSPORT`: `streamable-http` (default, can be omitted)
- `HOST`: `0.0.0.0` (default, can be omitted)
- `PORT`: Automatically set by Azure (don't override)
- `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`
- `ENABLE_ORYX_BUILD`: `true`
- `PYTHON_VERSION`: `3.11`

### Startup Command

The startup command should be set to:
```
startup.sh
```

This is configured automatically by the deployment script.

## Verify Deployment

1. **Check logs:**
   ```bash
   az webapp log tail --name openai-docs-mcp-server --resource-group your-resource-group
   ```

2. **Test the endpoint:**
   ```bash
   curl https://openai-docs-mcp-server.azurewebsites.net
   ```

3. **View in Azure Portal:**
   - Go to your Web App → Log stream
   - Check for any errors

## Troubleshooting

### Common Issues

1. **Module not found errors:**
   - Ensure `requirements-app.txt` is in the root directory
   - Check that all dependencies are listed
   - Review build logs in Azure Portal

2. **Port binding errors:**
   - Azure App Service automatically sets the PORT environment variable
   - Don't hardcode port numbers
   - Ensure startup script uses `$PORT`

3. **Import errors:**
   - Check PYTHONPATH in startup.sh
   - Verify file structure matches what's expected
   - Check that `mcp_server` directory is included in deployment

4. **Build failures:**
   - Check that Python version matches (3.11)
   - Verify requirements.txt is valid
   - Review build logs in Deployment Center

### Viewing Logs

```bash
# Stream logs
az webapp log tail --name openai-docs-mcp-server --resource-group your-resource-group

# Download logs
az webapp log download --name openai-docs-mcp-server --resource-group your-resource-group
```

## Updating the Deployment

To update the application:

1. Make your changes locally
2. Create a new deployment zip (excluding the same files)
3. Deploy using:
   ```bash
   az webapp deployment source config-zip \
     --name openai-docs-mcp-server \
     --resource-group your-resource-group \
     --src deploy.zip
   ```

## Cost Considerations

- The app runs on your existing App Service Plan
- No additional plan costs
- Only pay for compute resources used
- Consider scaling settings if needed

## Security

- The MCP server will be publicly accessible at `https://your-app-name.azurewebsites.net`
- Consider adding authentication if needed
- Use Azure Key Vault for sensitive configuration
- Enable HTTPS (enabled by default on Azure App Service)

## Next Steps

After deployment:
1. Test the MCP server endpoints
2. Configure custom domain if needed
3. Set up monitoring and alerts
4. Configure auto-scaling if needed
5. Set up CI/CD pipeline for automated deployments

