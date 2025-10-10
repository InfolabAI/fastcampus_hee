
import os

def write_file(file_path: str, content: str):
    """
    Writes content to a file.

    Args:
        file_path: The absolute path to the file to write to.
        content: The content to write to the file.

    Returns:
        A dictionary with a success or error message.
    """
    if not os.path.isabs(file_path):
        return {"error": f"Path must be absolute: {file_path}"}

    try:
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(file_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        is_new_file = not os.path.exists(file_path)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        if is_new_file:
            return {"message": f"Successfully created and wrote to new file: {file_path}"}
        else:
            return {"message": f"Successfully overwrote file: {file_path}"}

    except Exception as e:
        return {"error": f"Error writing to file: {e}"}

