# Cognition MCP Server

An MCP server for Claude Desktop that surfaces insights from your reading and viewing history.

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Get a NewsAPI key

Sign up for a free key at https://newsapi.org (100 requests/day on the free tier).

### 3. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cognition": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/mcp_server", "cognition-mcp"],
      "env": {
        "NEWSAPI_KEY": "your_key_here"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

### 4. Connect your accounts

In Claude Desktop:

- **Goodreads**: "Connect my Goodreads account, my username is johndoe"
- **Letterboxd (recent)**: "Connect my Letterboxd account, my username is johndoe"
- **Letterboxd (full history)**: Export your data from Letterboxd Settings → Import & Export, then:
  "Import my Letterboxd diary CSV from /path/to/diary.csv"

## Tools

| Tool | Description |
|------|-------------|
| `connect_goodreads(username)` | Load your Goodreads "read" shelf via RSS |
| `connect_letterboxd(username)` | Load recent Letterboxd diary via RSS (~50 entries) |
| `import_letterboxd_csv(file_path)` | Import complete Letterboxd history from exported diary.csv |
| `get_media_library()` | Show a summary of your cached books and films |
| `explore_idea(idea)` | Find connections between a personal idea and your media |
| `explore_current_events(topic)` | Find connections between current news and your media |

## Example prompts

- "I've been thinking about how institutions calcify and resist change even when it's harmful — how does this show up in what I've read and watched?"
- "How do current events around AI regulation connect to my media library?"
- "What books or films I've consumed deal most directly with the theme of loneliness in modern life?"
