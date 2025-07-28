#!/usr/bin/env python3
"""
Edit file tool implementation
"""

from pathlib import Path
from typing import Annotated
from fastmcp import Context


async def edit_file(
    file_path: Annotated[str, "The absolute path to the file to modify"],
    old_string: Annotated[str, "The text to replace"],
    new_string: Annotated[str, "The text to replace it with (must be different from old_string)"],
    replace_all: Annotated[bool, "Replace all occurrences of old_string (default false)"] = False,
    *,
    ctx: Context
) -> str:
    """Performs exact string replacements in files. 

Usage:
- You must use your `Read` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file. 
- When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after that tab is the actual file content to match. Never include any part of the line number prefix in the old_string or new_string.
- ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
- The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more surrounding context to make it unique or use `replace_all` to change every instance of `old_string`. 
- Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance."""
    await ctx.info(f"Editing file: {file_path}")
    
    if old_string == new_string:
        error_msg = "old_string and new_string must be different"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        path = Path(file_path)
        
        if not path.exists():
            error_msg = f"File does not exist: {file_path}"
            await ctx.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not path.is_file():
            error_msg = f"Path is not a file: {file_path}"
            await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = path.read_text(encoding='utf-8', errors='replace')
            await ctx.info("File contained non-UTF-8 characters, replaced with placeholders")
        
        if old_string not in content:
            error_msg = f"old_string not found in file: '{old_string[:100]}{'...' if len(old_string) > 100 else ''}'"
            await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        occurrence_count = content.count(old_string)
        
        if not replace_all and occurrence_count > 1:
            error_msg = f"old_string appears {occurrence_count} times in the file. Either provide a more unique string with more context or use replace_all=True to replace all occurrences."
            await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacements_made = occurrence_count
        else:
            new_content = content.replace(old_string, new_string, 1)
            replacements_made = 1
        
        path.write_text(new_content, encoding='utf-8')
        
        success_msg = f"Successfully replaced {replacements_made} occurrence{'s' if replacements_made != 1 else ''} in {file_path}"
        await ctx.info(success_msg)
        
        return success_msg
        
    except Exception as e:
        error_msg = f"Failed to edit file {file_path}: {str(e)}"
        await ctx.error(error_msg)
        raise