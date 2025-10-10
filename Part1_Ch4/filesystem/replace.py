
import os

def replace_in_file(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1):
    """
    Replaces text within a file.

    Args:
        file_path: The absolute path to the file to modify.
        old_string: The text to replace.
        new_string: The text to replace it with.
        expected_replacements: The number of replacements expected. If the actual number
                               of occurrences is different, the replacement is not performed.

    Returns:
        A dictionary with a success or error message.
    """
    if not os.path.isabs(file_path):
        return {"error": f"Path must be absolute: {file_path}"}

    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    if not os.path.isfile(file_path):
        return {"error": f"Path is not a file: {file_path}"}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        occurrences = content.count(old_string)

        if occurrences == 0:
            return {"error": "Failed to edit, could not find the string to replace."}

        if occurrences != expected_replacements:
            return {"error": f"Failed to edit, expected {expected_replacements} occurrences but found {occurrences}."}

        if old_string == new_string:
            return {"error": "No changes to apply. The old_string and new_string are identical."}

        new_content = content.replace(old_string, new_string, expected_replacements)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return {"message": f"Successfully modified file: {file_path} ({occurrences} replacements)."}

    except Exception as e:
        return {"error": f"Error processing file: {e}"}

