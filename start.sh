#!/bin/bash
set -e

echo "=== Starting OpenAI Docs MCP Server ==="

# Install dependencies inside the Azure container
echo "=== Installing requirements ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Starting FastMCP server ==="

# Start the MCP server using the Azure-provided port
fastmcp run mcp_server/server.py \
  --transport sse \
  --host 0.0.0.0 \
  --port $PORT
