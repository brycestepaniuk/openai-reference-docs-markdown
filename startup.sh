#!/bin/bash
set -e

echo "=== Starting OpenAI Docs MCP Server ==="

# Install requirements when the container starts
echo "=== Installing requirements ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Starting FastMCP server ==="

# Start your MCP server using FastMCP, binding to Azure's PORT
fastmcp run mcp_server/server.py \
  --transport sse \
  --host 0.0.0.0 \
  --port $PORT
