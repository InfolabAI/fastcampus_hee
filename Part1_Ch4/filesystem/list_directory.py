
import os
import pathlib
import fnmatch
from datetime import datetime

def list_directory(directory_path: str, ignore_patterns: list[str] = None):
    """
    Lists the contents of a directory, with optional ignore patterns.

    Args:
        directory_path: The absolute path to the directory to list.
        ignore_patterns: A list of glob patterns to ignore.

    Returns:
        A list of dictionaries, where each dictionary represents a file or directory.
    """
    if not os.path.isabs(directory_path):
        return {"error": f"Path must be absolute: {directory_path}"}

    if not os.path.exists(directory_path):
        return {"error": f"Directory not found: {directory_path}"}

    if not os.path.isdir(directory_path):
        return {"error": f"Path is not a directory: {directory_path}"}

    entries = []
    with os.scandir(directory_path) as it:
        for entry in it:
            should_ignore = False
            if ignore_patterns:
                for pattern in ignore_patterns:
                    if fnmatch.fnmatch(entry.name, pattern):
                        should_ignore = True
                        break
            if should_ignore:
                continue

            try:
                stat = entry.stat()
                is_dir = entry.is_dir()
                entries.append({
                    "name": entry.name,
                    "path": entry.path,
                    "is_directory": is_dir,
                    "size": stat.st_size if not is_dir else 0,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime)
                })
            except OSError as e:
                print(f"Error getting stats for {entry.path}: {e}")

    # Sort with directories first, then alphabetically
    entries.sort(key=lambda x: (not x["is_directory"], x["name"]))

    return entries

