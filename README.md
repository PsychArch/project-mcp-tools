# Project MCP Tools

[![PyPI](https://img.shields.io/pypi/v/project-mcp-tools.svg)](https://pypi.org/project/project-mcp-tools/)

MCP tools for software project development.

## Installation & Usage

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "project-mcp-tools": {
      "command": "uvx",
      "args": ["project-mcp-tools"]
    }
  }
}
```

## Available Tools

### File Operations
- `edit_file` - String replacements in files
- `multi_edit_file` - Multiple edits to a single file in one operation
- `read_file` - Read files with line numbers
- `write_file` - Write content to files
- `list_files` - List files and directories

### Search Tools
- `search_glob` - File pattern matching with glob patterns
- `grep` - Content search with regular expressions

