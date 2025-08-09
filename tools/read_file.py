#!/usr/bin/env python3
"""
Read file tool implementation
"""

import base64
import mimetypes
from pathlib import Path
from typing import Annotated, Union, List, Dict, Any
from fastmcp import Context


def _is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary by reading the first chunk and looking for null bytes."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(8192)  # Read first 8KB
            return b'\x00' in chunk
    except Exception:
        return False


def _detect_encoding(file_path: Path) -> str:
    """Detect file encoding, fallback to utf-8."""
    try:
        import chardet
        
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            # Only use detected encoding if confidence is high enough
            if confidence > 0.7 and encoding:
                return encoding
    except (ImportError, Exception):
        # chardet not available or detection failed
        pass
    
    # Simple heuristic: try UTF-8, then common encodings
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(1000)
            try:
                sample.decode('utf-8')
                return 'utf-8'
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                    try:
                        sample.decode(encoding)
                        return encoding
                    except UnicodeDecodeError:
                        continue
    except Exception:
        pass
    
    return 'utf-8'


def _is_jupyter_notebook(file_path: Path) -> bool:
    """Check if file is a Jupyter notebook."""
    return file_path.suffix.lower() == '.ipynb'


def _read_jupyter_notebook(file_path: Path) -> str:
    """Read Jupyter notebook and format cells."""
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        lines = [f"Jupyter Notebook: {file_path.name}"]
        lines.append("=" * 50)
        
        cells = notebook.get('cells', [])
        for i, cell in enumerate(cells, 1):
            cell_type = cell.get('cell_type', 'unknown')
            source = cell.get('source', [])
            
            lines.append(f"\n--- Cell {i} ({cell_type}) ---")
            
            if isinstance(source, list):
                lines.extend(source)
            else:
                lines.append(str(source))
            
            # Show outputs for code cells
            if cell_type == 'code' and 'outputs' in cell:
                outputs = cell['outputs']
                if outputs:
                    lines.append("\nOutput:")
                    for output in outputs:
                        if 'text' in output:
                            output_text = output['text']
                            if isinstance(output_text, list):
                                lines.extend(output_text)
                            else:
                                lines.append(str(output_text))
                        elif 'data' in output:
                            data = output['data']
                            if 'text/plain' in data:
                                plain_text = data['text/plain']
                                if isinstance(plain_text, list):
                                    lines.extend(plain_text)
                                else:
                                    lines.append(str(plain_text))
        
        return '\n'.join(lines)
        
    except Exception as e:
        return f"Error reading Jupyter notebook: {e}"


def _is_image_file(file_path: Path) -> bool:
    """Check if file is an image based on extension and mime type."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type is not None and mime_type.startswith('image/')


def _read_image_file(file_path: Path) -> Dict[str, Any]:
    """Read image file and return as base64 content block."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    with open(file_path, 'rb') as f:
        image_data = f.read()
    
    base64_data = base64.b64encode(image_data).decode('utf-8')
    
    return {
        "type": "image",
        "data": base64_data,
        "mimeType": mime_type
    }


async def read_file(
    file_path: Annotated[str, "The absolute path to the file to read"],
    offset: Annotated[int, "The line number to start reading from. Only provide if the file is too large to read at once"] = None,
    limit: Annotated[int, "The number of lines to read. Only provide if the file is too large to read at once."] = None,
    *,
    ctx: Context
) -> Union[str, Dict[str, Any]]:
    """Reads a file from the local filesystem. You can access any file directly by using this tool.
Assume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.

Usage:
- The file_path parameter must be an absolute path, not a relative path
- By default, it reads up to 2000 lines starting from the beginning of the file
- You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters
- Any lines longer than 2000 characters will be truncated
- Results are returned using cat -n format, with line numbers starting at 1
- This tool can read images (eg PNG, JPG, etc). 
- This tool can read Jupyter notebooks (.ipynb files) and returns all cells with their outputs, combining code, text, and visualizations.
- You have the capability to call multiple tools in a single response. It is always better to speculatively read multiple files as a batch that are potentially useful. 
- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents."""
    await ctx.info(f"Reading file: {file_path}")
    
    try:
        path = Path(file_path)
        
        # Validate file exists and is accessible
        if not path.exists():
            error_msg = f"File does not exist: {file_path}"
            await ctx.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not path.is_file():
            error_msg = f"Path is not a file: {file_path}"
            await ctx.error(error_msg)
            raise ValueError(error_msg)
        
        # Track this file as read in context state
        read_files = ctx.get_state("read_files") or set()
        read_files.add(file_path)
        ctx.set_state("read_files", read_files)
        await ctx.info(f"Tracking {file_path} as read")
        
        # Check file size and warn if large
        file_size = path.stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50MB
            await ctx.info(f"Warning: Large file detected ({file_size // (1024*1024)}MB). Consider using offset/limit parameters.")
        
        # Handle special file types
        if _is_image_file(path):
            await ctx.info("Detected image file, returning as base64 content block")
            return _read_image_file(path)
        
        if _is_jupyter_notebook(path):
            await ctx.info("Detected Jupyter notebook, formatting cells and outputs")
            return _read_jupyter_notebook(path)
        
        # Handle binary files
        if _is_binary_file(path):
            await ctx.info("Binary file detected, reading as hex dump")
            with open(path, 'rb') as f:
                if offset and limit:
                    f.seek(offset * 16)  # Assuming 16 bytes per line for hex dump
                    data = f.read(limit * 16)
                else:
                    data = f.read(32768)  # Read first 32KB for binary files
            
            hex_lines = []
            for i in range(0, len(data), 16):
                chunk = data[i:i+16]
                hex_part = ' '.join(f'{b:02x}' for b in chunk)
                ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                line_num = (offset or 0) + (i // 16) + 1
                hex_lines.append(f"     {line_num:04x}→{hex_part:<48} |{ascii_part}|")
            
            return '\n'.join(hex_lines) if hex_lines else "[Empty binary file]"
        
        # Handle text files with encoding detection
        detected_encoding = _detect_encoding(path)
        await ctx.info(f"Detected encoding: {detected_encoding}")
        
        try:
            content = path.read_text(encoding=detected_encoding)
        except UnicodeDecodeError:
            # Fallback to UTF-8 with error replacement
            content = path.read_text(encoding='utf-8', errors='replace')
            await ctx.info("File contained encoding issues, replaced problematic characters with placeholders")
        
        lines = content.splitlines()
        
        # Apply offset and limit
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
            # Default limit to prevent overwhelming output
            lines = lines[:2000]
        
        # Truncate overly long lines
        truncated_lines = []
        for line in lines:
            if len(line) > 2000:
                truncated_lines.append(line[:2000] + "... [line truncated]")
            else:
                truncated_lines.append(line)
        
        # Format output with line numbers
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
