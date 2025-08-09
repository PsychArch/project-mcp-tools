#!/usr/bin/env python3
"""
Grep tool implementation
"""

import os
import re
import glob as glob_module
from typing import Annotated, Optional
from fastmcp import Context


async def grep(
    pattern: Annotated[str, "The regular expression pattern to search for in file contents"],
    path: Annotated[Optional[str], "File or directory to search in (rg PATH). Defaults to current working directory."] = None,
    glob_pattern: Annotated[Optional[str], "Glob pattern to filter files (e.g. \"*.js\", \"*.{ts,tsx}\") - maps to rg --glob"] = None,
    type: Annotated[Optional[str], "File type to search (rg --type). Common types: js, py, rust, go, java, etc. More efficient than include for standard file types."] = None,
    output_mode: Annotated[Optional[str], "Output mode: \"content\" shows matching lines (supports -A/-B/-C context, -n line numbers, head_limit), \"files_with_matches\" shows file paths (supports head_limit), \"count\" shows match counts (supports head_limit). Defaults to \"files_with_matches\"."] = "files_with_matches",
    A: Annotated[Optional[int], "Number of lines to show after each match (rg -A). Requires output_mode: \"content\", ignored otherwise."] = None,
    B: Annotated[Optional[int], "Number of lines to show before each match (rg -B). Requires output_mode: \"content\", ignored otherwise."] = None,
    C: Annotated[Optional[int], "Number of lines to show before and after each match (rg -C). Requires output_mode: \"content\", ignored otherwise."] = None,
    i: Annotated[bool, "Case insensitive search (rg -i)"] = False,
    n: Annotated[bool, "Show line numbers in output (rg -n). Requires output_mode: \"content\", ignored otherwise."] = False,
    multiline: Annotated[bool, "Enable multiline mode where . matches newlines and patterns can span lines (rg -U --multiline-dotall). Default: false."] = False,
    head_limit: Annotated[Optional[int], "Limit output to first N lines/entries, equivalent to \"| head -N\". Works across all output modes: content (limits output lines), files_with_matches (limits file paths), count (limits count entries). When unspecified, shows all results from ripgrep."] = None,
    *,
    ctx: Context
) -> str:
    """A powerful search tool built on ripgrep

  Usage:
  - ALWAYS use Grep for search tasks. NEVER invoke `grep` or `rg` as a Bash command. The Grep tool has been optimized for correct permissions and access.
  - Supports full regex syntax (e.g., \"log.*Error\", \"function\\s+\\w+\")
  - Filter files with glob_pattern parameter (e.g., \"*.js\", \"**/*.tsx\") or type parameter (e.g., \"js\", \"py\", \"rust\")
  - Output modes: \"content\" shows matching lines, \"files_with_matches\" shows only file paths (default), \"count\" shows match counts
  - Pattern syntax: Uses ripgrep (not grep) - literal braces need escaping (use `interface\\{\\}` to find `interface{}` in Go code)
  - Multiline matching: By default patterns match within single lines only. For cross-line patterns like `struct \\{[\\s\\S]*?field`, use `multiline: true`"""
    await ctx.info(f"Searching for pattern: {pattern}")
    
    try:
        search_path = path if path else os.getcwd()
        
        if not os.path.exists(search_path):
            error_msg = f"Directory '{search_path}' does not exist"
            await ctx.error(error_msg)
            return f"Error: {error_msg}"
        
        # Compile regex with appropriate flags
        regex_flags = re.MULTILINE
        if i:
            regex_flags |= re.IGNORECASE
        if multiline:
            regex_flags |= re.DOTALL
        
        try:
            regex = re.compile(pattern, regex_flags)
        except re.error as e:
            error_msg = f"Invalid regex pattern '{pattern}': {str(e)}"
            await ctx.error(error_msg)
            return f"Error: {error_msg}"
        
        files_to_search = []
        
        # Handle file filtering by glob_pattern or type
        if type:
            # Expanded type mapping to match ripgrep's --type support
            type_extensions = {
                'js': ['*.js', '*.mjs'],
                'py': ['*.py', '*.pyx', '*.pyi'],
                'rust': ['*.rs'],
                'go': ['*.go'],
                'java': ['*.java'],
                'ts': ['*.ts'],
                'tsx': ['*.tsx'],
                'jsx': ['*.jsx'],
                'html': ['*.html', '*.htm'],
                'css': ['*.css', '*.scss', '*.sass', '*.less'],
                'json': ['*.json'],
                'yaml': ['*.yaml', '*.yml'],
                'xml': ['*.xml'],
                'md': ['*.md', '*.markdown'],
                'txt': ['*.txt'],
                'c': ['*.c', '*.h'],
                'cpp': ['*.cpp', '*.cc', '*.cxx', '*.hpp', '*.hh', '*.hxx'],
                'sh': ['*.sh', '*.bash'],
                'sql': ['*.sql'],
                'php': ['*.php'],
                'rb': ['*.rb'],
                'swift': ['*.swift'],
                'kotlin': ['*.kt', '*.kts'],
                'scala': ['*.scala'],
                'toml': ['*.toml'],
                'ini': ['*.ini', '*.cfg'],
                'dockerfile': ['Dockerfile', 'dockerfile'],
                'makefile': ['Makefile', 'makefile', '*.mk']
            }
            
            if type in type_extensions:
                for ext in type_extensions[type]:
                    full_pattern = os.path.join(search_path, "**", ext)
                    files_to_search.extend(glob_module.glob(full_pattern, recursive=True))
        elif glob_pattern:
            if "{" in glob_pattern and "}" in glob_pattern:
                base_pattern = glob_pattern.split("{")[0]
                extensions_part = glob_pattern.split("{")[1].split("}")[0]
                extensions = extensions_part.split(",")
                
                for ext in extensions:
                    pattern_with_ext = base_pattern + ext.strip()
                    full_pattern = os.path.join(search_path, "**", pattern_with_ext)
                    files_to_search.extend(glob_module.glob(full_pattern, recursive=True))
            else:
                full_pattern = os.path.join(search_path, "**", glob_pattern)
                files_to_search.extend(glob_module.glob(full_pattern, recursive=True))
        else:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        files_to_search.append(file_path)
        
        files_to_search = [f for f in files_to_search if os.path.isfile(f)]
        
        if not files_to_search:
            msg = f"No files found to search in '{search_path}'" + (f" with pattern '{glob_pattern}'" if glob_pattern else f" with type '{type}'" if type else "")
            await ctx.info(msg)
            return msg
        
        matching_results = []
        matching_files = []
        
        for file_path in files_to_search:
            try:
                if os.path.getsize(file_path) > 50 * 1024 * 1024:  # Skip files > 50MB
                    continue
                    
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    matches = list(regex.finditer(content))
                    if matches:
                        matching_files.append(file_path)
                        
                        if output_mode == "content":
                            lines = content.splitlines()
                            for match in matches:
                                start_pos = match.start()
                                line_num = content[:start_pos].count('\n') + 1
                                
                                # Calculate context lines
                                start_line = max(1, line_num - (B or C or 0))
                                end_line = min(len(lines), line_num + (A or C or 0))
                                
                                context_lines = []
                                for idx in range(start_line - 1, end_line):
                                    if idx < len(lines):
                                        line_prefix = f"{idx + 1}:" if n else ""
                                        context_lines.append(f"{line_prefix}{lines[idx]}")
                                
                                matching_results.extend(context_lines)
                        elif output_mode == "count":
                            matching_results.append(f"{len(matches)}:{file_path}")
                        
            except (IOError, OSError, UnicodeDecodeError):
                continue
        
        if not matching_files:
            msg = f"No files found containing pattern '{pattern}' in '{search_path}'" + (f" with pattern '{glob_pattern}'" if glob_pattern else f" with type '{type}'" if type else "")
            await ctx.info(msg)
            return msg
        
        # Sort by modification time
        matching_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Prepare results based on output mode
        if output_mode == "content":
            result_lines = matching_results
        elif output_mode == "count":
            result_lines = matching_results
        else:  # files_with_matches (default)
            result_lines = matching_files
        
        # Apply head limit if specified
        if head_limit and head_limit > 0:
            result_lines = result_lines[:head_limit]
        
        await ctx.info(f"Found {len(result_lines)} results")
        return "\n".join(result_lines)
        
    except Exception as e:
        error_msg = f"Error in grep: {str(e)}"
        await ctx.error(error_msg)
        raise
