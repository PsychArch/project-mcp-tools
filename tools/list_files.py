#!/usr/bin/env python3
"""
List files tool implementation
"""

from pathlib import Path
from typing import Annotated
from fastmcp import Context


async def list_files(
    path: Annotated[str, "The absolute path to the directory to list (must be absolute, not relative)"],
    ignore: Annotated[list[str], "List of glob patterns to ignore"] = None,
    *,
    ctx: Context
) -> list[str]:
    """Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path. You can optionally provide an array of glob patterns to ignore with the ignore parameter. You should generally prefer the Glob and Grep tools, if you know which directories to search."""
    await ctx.info(f"Listing files in: {path}")
    
    try:
        dir_path = Path(path)
        
        if not dir_path.exists():
            error_msg = f"Directory does not exist: {path}"
            await ctx.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not dir_path.is_dir():
            error_msg = f"Path is not a directory: {path}"
            await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        items = []
        for item in dir_path.iterdir():
            items.append(str(item))
        
        if ignore:
            from fnmatch import fnmatch
            filtered_items = []
            for item in items:
                item_name = Path(item).name
                should_ignore = False
                for pattern in ignore:
                    if fnmatch(item_name, pattern):
                        should_ignore = True
                        break
                if not should_ignore:
                    filtered_items.append(item)
            items = filtered_items
        
        items.sort()
        
        await ctx.info(f"Found {len(items)} items in {path}")
        return items
        
    except Exception as e:
        error_msg = f"Failed to list files in {path}: {str(e)}"
        await ctx.error(error_msg)
        raise