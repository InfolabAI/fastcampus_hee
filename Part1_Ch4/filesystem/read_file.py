
import os

def read_file(file_path: str, offset: int = None, limit: int = None):
    """
    Reads the content of a file, with optional line-based offset and limit.

    Args:
        file_path: The absolute path to the file to read.
        offset: The 0-based line number to start reading from.
        limit: The maximum number of lines to read.

    Returns:
        A dictionary containing the file content and other information.
    """
    if not os.path.isabs(file_path):
        return {"error": f"Path must be absolute: {file_path}"}

    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    if not os.path.isfile(file_path):
        return {"error": f"Path is not a file: {file_path}"}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        is_truncated = False

        if offset is not None and limit is not None:
            if offset < 0:
                return {"error": "Offset must be a non-negative number."}
            if limit <= 0:
                return {"error": "Limit must be a positive number."}

            start = offset
            end = offset + limit
            content_lines = lines[start:end]
            lines_shown = (start + 1, min(end, total_lines))
            is_truncated = total_lines > end
            next_offset = end

        else:
            content_lines = lines
            lines_shown = (1, total_lines)

        content = "".join(content_lines)

        result = {
            "llm_content": content,
            "is_truncated": is_truncated,
            "lines_shown": lines_shown,
            "original_line_count": total_lines,
        }

        if is_truncated:
            result["next_offset"] = next_offset
            result["message"] = f"Showing lines {lines_shown[0]}-{lines_shown[1]} of {total_lines}. To read more, use offset: {next_offset}."

        return result

    except Exception as e:
        return {"error": f"Error reading file: {e}"}

