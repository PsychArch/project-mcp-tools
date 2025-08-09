#!/usr/bin/env python3
"""
Write file tool implementation
"""

from pathlib import Path
from typing import Annotated
from fastmcp import Context
from . import validate_absolute_path


async def write_file(
    file_path: Annotated[str, "The absolute path to the file to write (must be absolute, not relative)"],
    content: Annotated[str, "The content to write to the file"],
    *,
    ctx: Context
) -> str:
    """Writes a file to the local filesystem.

Usage:
- This tool will overwrite the existing file if there is one at the provided path.
- If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail if you did not read the file first.
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
- Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked."""
    
    # Validate absolute path
    validate_absolute_path(file_path, "file writing")
    
    # Check if file was previously read (Read-before-Write validation)
    path = Path(file_path)
    if path.exists():
        read_files = ctx.get_state("read_files") or set()
        if file_path not in read_files:
            error_msg = f"Must read {file_path} before writing to existing file. Use read_file tool first."
            await ctx.error(error_msg)
            raise ValueError(error_msg)
    
    await ctx.info(f"Writing file: {file_path}")
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        
        success_msg = f"Successfully wrote {len(content)} characters to {file_path}"
        await ctx.info(success_msg)
        
        return success_msg
        
    except Exception as e:
        error_msg = f"Failed to write file {file_path}: {str(e)}"
        await ctx.error(error_msg)
        raise