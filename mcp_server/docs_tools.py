from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any

from .docs_index import (
    REPO_ROOT,
    SCOPES,
    SCOPE_PATHS,
    search_scope,
    read_section,
)


def register_docs_tools(mcp):
    """Attach all documentation-related MCP tools to the server instance.

    This function registers a small, high-signal set of tools that give agents
    good access to the local OpenAI documentation markdown.
    """

    @mcp.tool()
    def list_scopes() -> List[str]:
        """
        Return all available documentation scopes.

        These correspond to logical doc sets, for example:
        - "unified"
        - "api"
        - "guides"
        - "python"
        - "node"
        - "agents"
        - "cookbook"
        """
        return SCOPES

    @mcp.tool()
    def search_openai_docs(
        query: str,
        scope: str = "unified",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search the OpenAI docs for a free-text query within a scope.

        Args:
            query: Free-text search string.
            scope: One of the supported scopes (see ``list_scopes``).
            limit: Maximum number of matches to return.

        Returns:
            A list of matches. Each item has:
              - ``file``: relative path to the markdown file
              - ``line``: 1-based line number of the match
              - ``snippet``: short text around the match
        """
        if scope not in SCOPES:
            raise ValueError(f"Unknown scope: {scope!r}. Valid scopes: {SCOPES}")
        
        # Validate query
        query = query.strip() if query else ""
        if not query:
            return []
        
        # Validate and clamp limit
        if limit <= 0:
            limit = 10  # Default to 10 if invalid
        
        return search_scope(scope=scope, query=query, limit=limit)

    @mcp.tool()
    def get_openai_doc_section(
        file: str,
        start_line: int,
        end_line: Optional[int] = None,
        max_lines: int = 120,
    ) -> Dict[str, Any]:
        """Return a slice of a documentation file by line numbers.

        Args:
            file:
                Relative path from the repo root
                (for example ``"openai-docs-unified.md"``).
            start_line:
                First line to include (1-based, inclusive).
            end_line:
                Optional last line to include (1-based, inclusive). If omitted,
                a window defined by ``max_lines`` will be returned.
            max_lines:
                Used when ``end_line`` is ``None`` to avoid very large responses.

        Returns:
            Dict with:
              - ``file``
              - ``start_line``, ``end_line``
              - ``content``: the text slice
              - ``line_count``: number of lines in the slice
        """
        return read_section(file, start_line, end_line, max_lines)

    # -------------------------------------------------------------------------
    # New tool 1: get_last_update_metadata
    # -------------------------------------------------------------------------
    @mcp.tool()
    def get_last_update_metadata() -> Dict[str, Any]:
        """Return basic "last updated" information for the docs repo.

        This inspects the markdown files referenced by the configured scopes and
        reports the most recent filesystem modification time. It is intentionally
        simple and does not depend on git being available.

        Returns:
            Dict with keys:
              - ``repo_root``: absolute path to the repo root
              - ``last_modified_iso``: ISO-8601 timestamp in UTC
              - ``last_modified_unix``: float UNIX timestamp
              - ``last_modified_file``: relative path of the newest file
        """
        latest_mtime: float = 0.0
        latest_path: Optional[Path] = None

        # Walk all configured scope roots and look for markdown files.
        for roots in SCOPE_PATHS.values():
            for root in roots:
                if root.is_file():
                    candidates = [root]
                elif root.is_dir():
                    candidates = list(root.rglob("*.md"))
                else:
                    continue

                for path in candidates:
                    try:
                        mtime = path.stat().st_mtime
                    except OSError:
                        continue
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_path = path

        if latest_path is None:
            # Fallback: just use the repo root metadata.
            stat = REPO_ROOT.stat()
            latest_mtime = stat.st_mtime
            latest_path = REPO_ROOT

        dt = datetime.fromtimestamp(latest_mtime, tz=timezone.utc)

        try:
            rel_latest = str(latest_path.relative_to(REPO_ROOT))
        except ValueError:
            rel_latest = str(latest_path)

        return {
            "repo_root": str(REPO_ROOT),
            "last_modified_iso": dt.isoformat(),
            "last_modified_unix": latest_mtime,
            "last_modified_file": rel_latest,
        }

    # -------------------------------------------------------------------------
    # New tool 2: list_openai_doc_files
    # -------------------------------------------------------------------------
    @mcp.tool()
    def list_openai_doc_files(scope: str) -> List[str]:
        """List markdown documentation files for a given scope.

        Args:
            scope: One of the supported scopes (see ``list_scopes``).

        Returns:
            A sorted list of relative markdown file paths (from the repo root).
        """
        if scope not in SCOPE_PATHS:
            raise ValueError(f"Unknown scope: {scope!r}. Valid scopes: {SCOPES}")

        seen: set[Path] = set()
        files: List[Path] = []

        for root in SCOPE_PATHS[scope]:
            if root.is_file():
                candidate_files = [root]
            elif root.is_dir():
                candidate_files = list(root.rglob("*.md"))
            else:
                continue

            for path in candidate_files:
                rp = path.resolve()
                if rp not in seen:
                    seen.add(rp)
                    files.append(rp)

        result: List[str] = []
        for path in files:
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            result.append(str(rel))

        # Sort the string paths to ensure proper alphabetical order
        result.sort()

        return result

    # -------------------------------------------------------------------------
    # New tool 3: get_openai_doc_section_by_header
    # -------------------------------------------------------------------------
    def _extract_section_by_header_from_file(
        relative_file: str,
        header: str,
        header_level: Optional[int] = None,
        max_lines: int = 200,
    ) -> Optional[Dict[str, Any]]:
        """Internal helper to pull a section by markdown header.

        If ``header_level`` is provided, this looks specifically for that level,
        e.g. level 2 -> ``## Header``.

        If ``header_level`` is ``None``, it will automatically detect the
        header level by scanning all markdown headers in the file and picking
        the first one whose text matches ``header`` (case-insensitive).
        """
        path = REPO_ROOT / relative_file
        if not path.is_file():
            return None

        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        target_text = header.strip().lower()

        # First, find the header line and its actual level.
        start_idx: Optional[int] = None
        effective_level: Optional[int] = None

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped.startswith("#"):
                continue

            # Count leading hashes to determine this line's level.
            hash_count = len(stripped) - len(stripped.lstrip("#"))
            if hash_count <= 0:
                continue

            # Extract the visible header text after the hashes + a space (if any).
            text_part = stripped[hash_count:].lstrip()
            if not text_part:
                continue

            # If a specific level was requested, enforce it; otherwise accept
            # any level, as long as the text matches.
            if header_level is not None and hash_count != header_level:
                continue

            if text_part.lower() == target_text:
                start_idx = i
                effective_level = hash_count
                break

        if start_idx is None or effective_level is None:
            return None

        # Now find the end of this section: the next header of the same or
        # higher level, or EOF.
        end_idx = len(lines)
        for j in range(start_idx + 1, len(lines)):
            stripped = lines[j].lstrip()
            if stripped.startswith("#"):
                hash_count = len(stripped) - len(stripped.lstrip("#"))
                if hash_count <= effective_level:
                    end_idx = j
                    break

        # Enforce max_lines limit.
        if max_lines is not None and (end_idx - start_idx) > max_lines:
            end_idx = start_idx + max_lines

        start_line = start_idx + 1  # 1-based
        # end_idx is exclusive (points to next header or EOF), so the last included line is end_idx - 1
        # In 1-based indexing, that's line number end_idx
        end_line = end_idx  # 1-based, inclusive (last line of the section)

        content = "\n".join(lines[start_idx:end_idx])

        return {
            "file": relative_file,
            "start_line": start_line,
            "end_line": end_line,
            "content": content,
            "line_count": end_line - start_line + 1,
        }

    @mcp.tool()
    def get_openai_doc_section_by_header(
        header: str,
        scope: str = "unified",
        header_level: Optional[int] = None,
        max_lines: int = 200,
    ) -> Dict[str, Any]:
        """Return a documentation section identified by its markdown header.

        Args:
            header:
                The header text, without ``#`` characters. For example
                ``"Vision"`` or ``"Chat Completions"``.
            scope:
                One of the supported scopes (default: ``"unified"``).
            header_level:
                Optional explicit markdown header level to match.
                - If provided (1–6): require exactly that level
                  (e.g. 2 -> ``## Header``).
                - If ``None``: automatically detect the header level by finding
                  the first matching header text, regardless of level.
            max_lines:
                Safety cap on section length. The section will be truncated if it
                would exceed this many lines.

        Returns:
            A dict similar to ``get_openai_doc_section`` with:
              - ``file``: relative file path
              - ``start_line``, ``end_line``
              - ``content``
              - ``line_count``

        Raises:
            ValueError if the scope is unknown or if no matching header is found.
        """
        if scope not in SCOPES:
            raise ValueError(f"Unknown scope: {scope!r}. Valid scopes: {SCOPES}")

        # Strategy:
        #   1. Use the existing text search to find likely files.
        #   2. For each candidate file, try to extract a section whose header
        #      text matches `header`. If `header_level` is None, any level is
        #      accepted; otherwise an exact level match is required.
        #   3. Return the first successful match.
        # Call search_scope directly instead of the tool function to avoid recursion
        search_results = search_scope(scope=scope, query=header, limit=8)

        for match in search_results:
            relative_file = match.get("file")
            if not relative_file:
                continue

            section = _extract_section_by_header_from_file(
                relative_file=relative_file,
                header=header,
                header_level=header_level,
                max_lines=max_lines,
            )
            if section is not None:
                return section

        level_desc = (
            "any level" if header_level is None else f"level {header_level}"
        )
        raise ValueError(
            f"Unable to find header {header!r} at {level_desc} in scope {scope!r}."
        )
