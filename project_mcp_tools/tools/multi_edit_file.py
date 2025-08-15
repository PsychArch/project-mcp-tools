#!/usr/bin/env python3
"""
MultiEdit file tool implementation
"""

from pathlib import Path
from typing import Annotated, List, Dict, Any
from fastmcp import Context
from . import validate_absolute_path
from .session_manager import session_manager


async def multi_edit_file(
    file_path: Annotated[str, "The absolute path to the file to modify"],
    edits: Annotated[List[Dict[str, Any]], "Array of edit operations to perform sequentially on the file"],
    *,
    ctx: Context
) -> str:
    """This is a tool for making multiple edits to a single file in one operation. It is built on top of the Edit tool and allows you to perform multiple find-and-replace operations efficiently. Prefer this tool over the Edit tool when you need to make multiple edits to the same file.

Before using this tool:

1. Use the Read tool to understand the file's contents and context
2. Verify the directory path is correct

To make multiple file edits, provide the following:
1. file_path: The absolute path to the file to modify (must be absolute, not relative)
2. edits: An array of edit operations to perform, where each edit contains:
   - old_string: The text to replace (must match the file contents exactly, including all whitespace and indentation)
   - new_string: The edited text to replace the old_string
   - replace_all: Replace all occurences of old_string. This parameter is optional and defaults to false.

IMPORTANT:
- All edits are applied in sequence, in the order they are provided
- Each edit operates on the result of the previous edit
- All edits must be valid for the operation to succeed - if any edit fails, none will be applied
- This tool is ideal when you need to make several changes to different parts of the same file

CRITICAL REQUIREMENTS:
1. All edits follow the same requirements as the single Edit tool
2. The edits are atomic - either all succeed or none are applied
3. Plan your edits carefully to avoid conflicts between sequential operations

WARNING:
- The tool will fail if edits.old_string doesn't match the file contents exactly (including whitespace)
- The tool will fail if edits.old_string and edits.new_string are the same
- Since edits are applied in sequence, ensure that earlier edits don't affect the text that later edits are trying to find

When making edits:
- Ensure all edits result in idiomatic, correct code
- Do not leave the code in a broken state
- Always use absolute file paths (starting with /)
- Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
- Use replace_all for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.

If you want to create a new file, use:
- A new file path, including dir name if needed
- First edit: empty old_string and the new file's contents as new_string
- Subsequent edits: normal edit operations on the created content"""
    
    # Validate absolute path
    validate_absolute_path(file_path, "multi-edit file operation")
    
    # Check if file was previously read (Read-before-Edit validation)
    if not session_manager.is_file_read(ctx.session_id, file_path):
        error_msg = f"Must read {file_path} before editing. Use read_file tool first."
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    await ctx.info(f"Performing multi-edit on file: {file_path}")
    
    if not edits:
        error_msg = "No edits provided"
        await ctx.error(error_msg)
        raise ValueError(error_msg)
    
    # Validate all edits first
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            error_msg = f"Edit {i+1} must be a dictionary"
            await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        if "old_string" not in edit or "new_string" not in edit:
            error_msg = f"Edit {i+1} must contain 'old_string' and 'new_string'"
            await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        if edit["old_string"] == edit["new_string"]:
            error_msg = f"Edit {i+1}: old_string and new_string must be different"
            await ctx.error(error_msg)
            raise ValueError(error_msg)
    
    try:
        path = Path(file_path)
        
        # Handle new file creation case
        if not path.exists() and len(edits) > 0 and edits[0]["old_string"] == "":
            # Creating a new file
            await ctx.info(f"Creating new file: {file_path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            content = edits[0]["new_string"]
            remaining_edits = edits[1:]
        else:
            # Editing existing file
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
            
            remaining_edits = edits
        
        # Apply all edits in sequence
        total_replacements = 0
        
        for i, edit in enumerate(remaining_edits):
            old_string = edit["old_string"]
            new_string = edit["new_string"]
            replace_all = edit.get("replace_all", False)
            
            if old_string not in content:
                error_msg = f"Edit {i+1}: old_string not found in file: '{old_string[:100]}{'...' if len(old_string) > 100 else ''}'"
                await ctx.error(error_msg)
                raise ValueError(error_msg)
            
            occurrence_count = content.count(old_string)
            
            if not replace_all and occurrence_count > 1:
                error_msg = f"Edit {i+1}: old_string appears {occurrence_count} times in the file. Either provide a more unique string with more context or use replace_all=True to replace all occurrences."
                await ctx.error(error_msg)
                raise ValueError(error_msg)
            
            if replace_all:
                content = content.replace(old_string, new_string)
                replacements_made = occurrence_count
            else:
                content = content.replace(old_string, new_string, 1)
                replacements_made = 1
            
            total_replacements += replacements_made
            await ctx.info(f"Edit {i+1}: Replaced {replacements_made} occurrence{'s' if replacements_made != 1 else ''}")
        
        # Write the final content
        path.write_text(content, encoding='utf-8')
        
        success_msg = f"Successfully applied {len(edits)} edits with {total_replacements} total replacements in {file_path}"
        await ctx.info(success_msg)
        
        return success_msg
        
    except Exception as e:
        error_msg = f"Failed to perform multi-edit on file {file_path}: {str(e)}"
        await ctx.error(error_msg)
        raise
