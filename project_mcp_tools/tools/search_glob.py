#!/usr/bin/env python3
"""
Search glob tool implementation
"""

import os
import glob
from typing import Annotated, Optional
from fastmcp import Context


async def search_glob(
    pattern: Annotated[str, "The glob pattern to match files against"],
    path: Annotated[Optional[str], "The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter \"undefined\" or \"null\" - simply omit it for the default behavior. Must be a valid directory path if provided."] = None,
    *,
    ctx: Context
) -> str:
    """- Fast file pattern matching tool that works with any codebase size
- Supports glob patterns like \"**/*.js\" or \"src/**/*.ts\"
- Returns matching file paths sorted by modification time
- Use this tool when you need to find files by name patterns
- It is always better to speculatively perform multiple searches as a batch that are potentially useful."""
    await ctx.info(f"Searching for files matching pattern: {pattern}")
    
    try:
        search_path = path if path else os.getcwd()
        
        if not os.path.exists(search_path):
            error_msg = f"Directory '{search_path}' does not exist"
            await ctx.error(error_msg)
            return f"Error: {error_msg}"
        
        original_cwd = os.getcwd()
        try:
            os.chdir(search_path)
            
            matches = []
            if "**" in pattern:
                matches = glob.glob(pattern, recursive=True)
            else:
                matches = glob.glob(pattern)
            
            absolute_matches = []
            for match in matches:
                if os.path.isfile(match):
                    absolute_path = os.path.abspath(match)
                    absolute_matches.append(absolute_path)
            
            absolute_matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            if not absolute_matches:
                msg = f"No files found matching pattern '{pattern}' in '{search_path}'"
                await ctx.info(msg)
                return msg
            
            result_lines = []
            for file_path in absolute_matches:
                result_lines.append(file_path)
            
            await ctx.info(f"Found {len(absolute_matches)} matching files")
            return "\n".join(result_lines)
            
        finally:
            os.chdir(original_cwd)
            
    except Exception as e:
        error_msg = f"Error in search_glob: {str(e)}"
        await ctx.error(error_msg)
        raise
