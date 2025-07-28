#!/usr/bin/env python3
"""
Read file tool implementation
"""

from pathlib import Path
from typing import Annotated
from fastmcp import Context


async def read_file(
    file_path: Annotated[str, "The absolute path to the file to read"],
    offset: Annotated[int, "The line number to start reading from. Only provide if the file is too large to read at once"] = None,
    limit: Annotated[int, "The number of lines to read. Only provide if the file is too large to read at once."] = None,
    *,
    ctx: Context
) -> str:
    """Reads a file from the local filesystem. You can access any file directly by using this tool.
Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

Usage:
- The file_path parameter must be an absolute path, not a relative path
- By default, it reads up to 2000 lines starting from the beginning of the file
- You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters
- Any lines longer than 2000 characters will be truncated
- Results are returned using cat -n format, with line numbers starting at 1
- This tool allows Claude Code to read images (eg PNG, JPG, etc). When reading an image file the contents are presented visually as Claude Code is a multimodal LLM.
- This tool can read PDF files (.pdf). PDFs are processed page by page, extracting both text and visual content for analysis.
- For Jupyter notebooks (.ipynb files), use the NotebookRead instead
- You have the capability to call multiple tools in a single response. It is always better to speculatively read multiple files as a batch that are potentially useful. 
- You will regularly be asked to read screenshots. If the user provides a path to a screenshot ALWAYS use this tool to view the file at the path. This tool will work with all temporary file paths like /var/folders/123/abc/T/TemporaryItems/NSIRD_screencaptureui_ZfB1tD/Screenshot.png
- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents."""
    await ctx.info(f"Reading file: {file_path}")
    
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
        
        lines = content.splitlines()
        
        if offset is not None:
            if offset < 1:
                offset = 1
            start_idx = offset - 1
            lines = lines[start_idx:]
        else:
            start_idx = 0
            
        if limit is not None and limit > 0:
            lines = lines[:limit]
        elif limit is None:
            lines = lines[:2000]
        
        truncated_lines = []
        for line in lines:
            if len(line) > 2000:
                truncated_lines.append(line[:2000] + "... [line truncated]")
            else:
                truncated_lines.append(line)
        
        if truncated_lines:
            formatted_lines = []
            for i, line in enumerate(truncated_lines, start=start_idx + 1):
                formatted_lines.append(f"     {i}→{line}")
            
            result = "\n".join(formatted_lines)
        else:
            result = "[Empty file]"
        
        await ctx.info(f"Successfully read {len(lines)} lines from {file_path}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to read file {file_path}: {str(e)}"
        await ctx.error(error_msg)
        raise