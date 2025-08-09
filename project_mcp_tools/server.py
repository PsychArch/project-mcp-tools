#!/usr/bin/env python3
"""
Project MCP Tools

A single executable entry point providing all MCP tools.
"""

from fastmcp import FastMCP
from .tools.edit_file import edit_file
from .tools.multi_edit_file import multi_edit_file
from .tools.read_file import read_file
from .tools.write_file import write_file
from .tools.list_files import list_files
from .tools.search_glob import search_glob
from .tools.grep import grep


def create_server() -> FastMCP:
    """Create a FastMCP server with all tools."""
    
    # Create server
    mcp_server = FastMCP(
        name="Project MCP Tools",
        mask_error_details=False
    )
    
    # Register all tools using mcp.tool decorator
    mcp_server.tool(edit_file)
    mcp_server.tool(multi_edit_file)
    mcp_server.tool(read_file)
    mcp_server.tool(write_file)
    mcp_server.tool(list_files)
    mcp_server.tool(search_glob)
    mcp_server.tool(grep)
    
    return mcp_server


def main():
    """Main entry point."""
    # Create and start server
    server = create_server()
    
    # Run the server
    print("\nStarting Project MCP Tools...")
    print("Press Ctrl+C to stop")
    
    try:
        server.run(show_banner=False)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
