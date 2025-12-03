"""
OpenAI Docs MCP Server

Exposes tools for searching and reading your local
OpenAI documentation markdown files.
"""

from __future__ import annotations

import os
import sys

# --- Ensure the project root is on sys.path ---------------------------------
# When Azure runs this via `fastmcp run mcp_server/server.py`, Python sets
# sys.path[0] to ".../mcp_server", so `import mcp_server` fails.
# We fix that by adding the parent directory (project root) to sys.path.
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ---------------------------------------------------------------------------

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp_server.docs_tools import register_docs_tools  # now importable


# Create the MCP instance and register all tools.
# The fastmcp CLI will look for this `mcp` object.
mcp = FastMCP(
    "openai-docs-demo",
    transport_security=TransportSecuritySettings(
        # Keep DNS rebinding protection ON, but explicitly allow your Azure host.
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "openai-docs-mcp.azurewebsites.net",
            "openai-docs-mcp.azurewebsites.net:*",
        ],
        # Origins are mainly relevant for browser-based clients, but harmless to set.
        allowed_origins=[
            "https://openai-docs-mcp.azurewebsites.net",
        ],
    ),
)

# Register your OpenAI docs tools with this MCP instance.
register_docs_tools(mcp)


if __name__ == "__main__":
    """
    Entry point for running the server directly (e.g. local dev).

    - `python -m mcp_server.server`  → stdio transport (Cursor)
    - Direct script run              → also works because of sys.path fix
    - `fastmcp run mcp_server/server.py --transport sse ...`
      imports this file, finds `mcp`, and calls `mcp.run(...)` itself.
    """
    mcp.run()
