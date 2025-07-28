#!/usr/bin/env python3
"""
Unified MCP Tools Server

A single executable entry point providing all MCP tools.
"""

from fastmcp import FastMCP
from tools.edit_file import edit_file
from tools.read_file import read_file
from tools.write_file import write_file
from tools.list_files import list_files
from tools.search_glob import search_glob
from tools.grep import grep


def create_unified_server() -> FastMCP:
    """Create a unified FastMCP server with all tools."""
    
    # Create unified server
    unified_mcp = FastMCP(
        name="Unified MCP Tools Server",
        mask_error_details=False
    )
    
    # Register all tools using mcp.tool decorator
    unified_mcp.tool(edit_file)
    unified_mcp.tool(read_file)
    unified_mcp.tool(write_file)
    unified_mcp.tool(list_files)
    unified_mcp.tool(search_glob)
    unified_mcp.tool(grep)
    
    # Add unified server info resource
    @unified_mcp.resource("config://unified-server")
    def get_unified_server_config() -> dict:
        """Provide unified server configuration information."""
        return {
            "name": "Unified MCP Tools Server",
            "version": "1.0.0",
            "description": "Single executable providing all MCP tools",
            "available_tools": ["edit_file", "read_file", "write_file", "list_files", "search_glob", "grep"],
            "total_tools": 6
        }
    
    print("Unified server created with all tools: edit_file, read_file, write_file, list_files, search_glob, grep")
    
    return unified_mcp


def main():
    """Main entry point."""
    # Create and start unified server
    unified_server = create_unified_server()
    
    # Run the unified server
    print("\nStarting Unified MCP Tools Server...")
    print("Press Ctrl+C to stop")
    
    try:
        unified_server.run(show_banner=False)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()