from pathlib import Path
from typing import List, Dict, Optional

# Root of your repo (mcp_server folder is inside it)
REPO_ROOT = Path(__file__).resolve().parent.parent

# Supported scopes
SCOPES = ["unified", "api", "guides", "python", "node", "agents", "cookbook"]

# Map scopes → folder paths
SCOPE_PATHS: Dict[str, List[Path]] = {
    "unified": [REPO_ROOT / "openai-docs-unified.md"],
    "api": [REPO_ROOT / "openai-docs-api-reference"],
    "guides": [REPO_ROOT / "openai-docs-guides"],
    "python": [REPO_ROOT / "openai-python-docs"],
    "node": [REPO_ROOT / "openai-node-js-docs"],
    "agents": [REPO_ROOT / "openai-agents-python-docs"],
    "cookbook": [REPO_ROOT / "openai-cookbook"],
}


# ---------------------------------------------------------
# Core indexing functions
# ---------------------------------------------------------

def get_files_for_scope(scope: str) -> List[Path]:
    """Return all markdown files for the selected scope."""
    if scope not in SCOPE_PATHS:
        raise ValueError(f"Unknown scope: {scope}")

    files: List[Path] = []
    for path in SCOPE_PATHS[scope]:
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            files.extend(path.glob("**/*.md"))

    return files


def search_in_file(file_path: Path, query: str) -> List[Dict]:
    """Search a single Markdown file for a substring."""
    results: List[Dict] = []
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()  # Use splitlines() for consistency

    for i, line in enumerate(lines):
        if query.lower() in line.lower():
            # Return relative path from REPO_ROOT
            try:
                rel_file = str(file_path.relative_to(REPO_ROOT))
            except ValueError:
                rel_file = str(file_path)
            
            results.append({
                "file": rel_file,  # Relative path, not absolute
                "line": i + 1,        # 1-based
                "snippet": line.strip()
            })

    return results


def search_scope(scope: str, query: str, limit: int = 20) -> List[Dict]:
    """Search across all files in a documentation scope."""
    # Early return for empty query
    if not query or not query.strip():
        return []
    
    # Clamp limit to valid range
    if limit <= 0:
        limit = 20  # Default limit
    
    results: List[Dict] = []
    files = get_files_for_scope(scope)

    for file in files:
        hits = search_in_file(file, query)
        results.extend(hits)
        if len(results) >= limit:
            break

    return results[:limit]


# ---------------------------------------------------------
# Section reading
# ---------------------------------------------------------

def read_section(
    file: str,
    start_line: int,
    end_line: Optional[int] = None,
    max_lines: int = 80,
) -> Dict:
    """
    Read a slice of a docs file by line range.

    Args:
        file: relative path (e.g. 'openai-docs-unified.md'
              or 'openai-python-docs/README.md')
        start_line: first line to include (1-based)
        end_line: optional last line (1-based). If None, uses max_lines window.
        max_lines: used when end_line is None, to avoid huge responses.

    Returns:
        dict with:
          - file: relative path from REPO_ROOT
          - start_line, end_line
          - content: the text slice
          - line_count: number of lines returned
    """
    # Resolve relative to repo root if needed
    path = Path(file)
    if not path.is_absolute():
        path = REPO_ROOT / path

    if not path.exists():
        raise FileNotFoundError(f"Docs file not found: {file}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    if start_line < 1:
        start_line = 1

    start_idx = start_line - 1
    if start_idx >= len(lines):
        raise ValueError(
            f"start_line {start_line} is beyond end of file "
            f"(file has {len(lines)} lines)"
        )

    if end_line is not None:
        if end_line < start_line:
            raise ValueError("end_line must be >= start_line")
        end_idx = min(end_line, len(lines))
    else:
        end_idx = min(start_line - 1 + max_lines, len(lines))

    slice_lines = lines[start_idx:end_idx]
    content = "\n".join(slice_lines)

    # Make file path relative for cleaner output
    try:
        rel_file = str(path.relative_to(REPO_ROOT))
    except ValueError:
        rel_file = str(path)

    return {
        "file": rel_file,
        "start_line": start_line,
        "end_line": end_idx,
        "content": content,
        "line_count": len(slice_lines),
    }
