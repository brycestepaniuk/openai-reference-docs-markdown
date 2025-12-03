"""
Azure App Service entry point for MCP server.
This file serves as the main entry point for Azure App Service.
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the MCP server
from mcp_server.server import mcp

if __name__ == "__main__":
    # Azure App Service environment
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"Starting MCP server on {host}:{port} with {transport} transport")
    mcp.run(transport=transport, host=host, port=port)

