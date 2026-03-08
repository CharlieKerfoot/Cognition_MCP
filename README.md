# Cognition MCP Server

An MCP server for Claude Desktop that surfaces insights from your reading, viewing, and thinking history — connecting your Goodreads books, Letterboxd films, and Obsidian notes to each other and to current events.

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Get a NewsAPI key

Sign up for a free key at https://newsapi.org (100 requests/day on the free tier).

### 3. Configure Claude Desktop

Claude Desktop launches MCP servers with a minimal PATH that may not include `uv`. A wrapper script handles this by sourcing your shell profile first.

Make the included wrapper executable:

```bash
chmod +x /absolute/path/to/mcp_server/run.sh
```

Then edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cognition": {
      "command": "/absolute/path/to/mcp_server/run.sh",
      "args": [],
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

- **Goodreads**: "Connect my Goodreads account: https://www.goodreads.com/review/list/167725774-your-name"
- **Letterboxd (recent)**: "Connect my Letterboxd account, my username is johndoe"
- **Letterboxd (full history)**: Export your data from Letterboxd Settings → Import & Export, unzip, then upload `diary.csv` to Claude and say: "Import my Letterboxd diary CSV" (Claude will read the file and pass the contents automatically)
- **Obsidian**: "Connect my Obsidian vault at /Users/you/Documents/MyVault"

## Tools

| Tool | Description |
|------|-------------|
| `connect_goodreads(profile_url_or_id)` | Load your Goodreads "read" shelf via RSS |
| `connect_letterboxd(username)` | Load recent Letterboxd diary via RSS (~50 entries) |
| `import_letterboxd_csv(csv_content)` | Import complete Letterboxd history from exported diary.csv content |
| `connect_obsidian(vault_path)` | Load all notes from an Obsidian vault |
| `get_media_library()` | Show a summary of your cached books, films, and notes |
| `explore_idea(idea)` | Find connections between a personal idea and your books, films, and notes |
| `explore_current_events(topic)` | Find connections between current news and your books, films, and notes |

## Example prompts

- "I've been thinking about how institutions calcify and resist change even when it's harmful — how does this show up in what I've read, watched, and written?"
- "How do current events around AI regulation connect to my media library?"
- "What's the most surprising connection between my own notes and something I've read or watched?"
- "What books or films I've consumed deal most directly with the theme of loneliness in modern life?"
