# Tools package

from pathlib import Path

def validate_absolute_path(file_path: str, operation: str = "operation") -> None:
    """Validate that a file path is absolute (not relative).
    
    Args:
        file_path: The file path to validate
        operation: Description of the operation for error messages
        
    Raises:
        ValueError: If the path is not absolute
    """
    path = Path(file_path)
    if not path.is_absolute():
        raise ValueError(f"Path must be absolute, not relative, for {operation}: {file_path}")

from .edit_file import edit_file
from .multi_edit_file import multi_edit_file
from .read_file import read_file
from .write_file import write_file
from .list_files import list_files
from .search_glob import search_glob
from .grep import grep

__all__ = [
    'edit_file',
    'multi_edit_file',
    'read_file', 
    'write_file',
    'list_files',
    'search_glob',
    'grep'
]