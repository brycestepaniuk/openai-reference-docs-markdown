from mcp.server.fastmcp import FastMCP
from pathlib import Path
from typing import List, Dict, Literal

# Root of your repo (mcp_server is inside it)
REPO_ROOT = Path(__file__).resolve().parent.parent

# The different doc "scopes" your tool can search
Scope = Literal["unified", "api", "guides", "python", "node", "agents", "cookbook"]

SCOPE_PATHS = {
    # Single combined markdown file
    "unified": [REPO_ROOT / "openai-docs-unified.md"],
    # Individual doc trees
    "api": [REPO_ROOT / "openai-docs-api-reference"],
    "guides": [REPO_ROOT / "openai-docs-guides"],
    "python": [REPO_ROOT / "openai-python-docs"],
    "node": [REPO_ROOT / "openai-node-js-docs"],
    "agents": [REPO_ROOT / "openai-agents-python-docs"],
    "cookbook": [REPO_ROOT / "openai-cookbook"],
}

# This is the name Cursor will show for your server
mcp = FastMCP("openai-docs-demo")


@mcp.tool()
def echo(message: str) -> str:
    """
    A simple echo tool to verify MCP wiring.
    """
    return f"You said: {message}"


@mcp.tool()
def search_openai_docs(query: str, scope: Scope = "unified", limit: int = 5) -> List[Dict]:
    """
    Search the locally mirrored OpenAI documentation.

    Args:
        query: Search text (case insensitive).
        scope: Which docs to search:
            - "unified" (default): openai-docs-unified.md
            - "api":      openai-docs-api-reference/
            - "guides":   openai-docs-guides/
            - "python":   openai-python-docs/
            - "node":     openai-node-js-docs/
            - "agents":   openai-agents-python-docs/
            - "cookbook": openai-cookbook/
        limit: Maximum number of results to return.

    Returns:
        A list of results. Each result is a dict with:
        - file: relative path to the markdown file
        - scope: the scope searched
        - start_line, end_line: line numbers of the snippet (1-based)
        - snippet: markdown text snippet around the match
        - score: simple relevance score (higher is better)
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    # Safety on limit
    if limit <= 0:
        limit = 5

    # Resolve which paths to search
    paths = SCOPE_PATHS.get(scope, SCOPE_PATHS["unified"])

    results: List[Dict] = []

    def add_result(path: Path, line_idx: int, lines: List[str]) -> None:
        # Grab a small window of context around the matching line
        start = max(0, line_idx - 3)
        end = min(len(lines), line_idx + 4)
        snippet = "\n".join(lines[start:end])

        # Simple score: earlier matches in file rank higher
        score = 1.0 / (1 + line_idx)

        results.append(
            {
                "file": str(path.relative_to(REPO_ROOT)),
                "scope": scope,
                "start_line": start + 1,  # convert to 1-based
                "end_line": end,
                "snippet": snippet,
                "score": score,
            }
        )

    # Walk each path: either a file or a directory of .md files
    for base in paths:
        if base.is_file():
            candidates = [base]
        elif base.is_dir():
            candidates = list(base.rglob("*.md"))
        else:
            # Path doesn't exist; skip
            continue

        for md_file in candidates:
            try:
                text = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                # Skip unreadable files
                continue

            lines = text.splitlines()
            for idx, line in enumerate(lines):
                if query_lower in line.lower():
                    add_result(md_file, idx, lines)

    # Sort by score (desc) and trim to limit
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


if __name__ == "__main__":
    # Run MCP server over stdio (how Cursor connects)
    mcp.run()
