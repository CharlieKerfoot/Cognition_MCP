# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python MCP server for Claude Desktop that surfaces insights from a user's reading (Goodreads), viewing (Letterboxd), and personal notes (Obsidian) history, connecting them to current events via NewsAPI. The goal is to generate novel insights connecting recent ideas or current events to previously consumed media. This is a smaller experiment, which, if successful, will be developed into a larger-scale app.

## Commands

```bash
# Install dependencies
uv sync

# Run the server directly (for testing)
uv run cognition-mcp

# The server is normally launched by Claude Desktop via run.sh (sources ~/.zshrc first to ensure uv is on PATH)
```

## Architecture

All source code lives in `src/cognition_mcp/`. The server uses `FastMCP` from the `mcp` package and runs over stdio transport.

**Module responsibilities:**
- `server.py` — MCP tool definitions; orchestrates calls to other modules and reads/writes via `storage`. Contains `_slim_library()` which truncates note content (600 chars), book descriptions (200 chars), and reviews (300 chars) before returning data to stay under the 1MB MCP tool result limit.
- `storage.py` — Persists the library as JSON at `~/.cognition_mcp/library.json`; schema: `{books: [], films: [], notes: [], meta: {}}`. `load()` migrates existing files missing the `notes` key.
- `goodreads.py` — Extracts numeric user ID from a Goodreads profile URL or bare ID string (no HTTP resolution needed), then fetches the "read" shelf via RSS/feedparser.
- `letterboxd.py` — Fetches Letterboxd diary via RSS (recent ~50 entries) or parses exported `diary.csv` content passed as a string; deduplicates by `(title, year, watch_date)`.
- `obsidian.py` — Recursively scans an Obsidian vault for `.md` files; extracts title, tags (YAML frontmatter + inline `#tags`), modified date, and full content. Skips hidden directories.
- `news.py` — Fetches articles from NewsAPI (`NEWSAPI_KEY` env var required, 100 req/day free tier).

**Data flow for `explore_*` tools:** tools load the full library from disk, slim it via `_slim_library()`, then return it as JSON alongside an instruction string — Claude (not the server) performs the actual analysis.

**Key input conventions:**
- `connect_goodreads` — accepts a full profile URL (`https://www.goodreads.com/review/list/167725774-name`) or bare numeric ID
- `import_letterboxd_csv` — accepts raw CSV file *content* as a string (not a file path), because Claude Desktop's uploaded file paths are not accessible to the MCP server process

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "cognition": {
      "command": "/absolute/path/to/mcp_server/run.sh",
      "args": [],
      "env": { "NEWSAPI_KEY": "your_key_here" }
    }
  }
}
```

After editing the config, restart Claude Desktop.
