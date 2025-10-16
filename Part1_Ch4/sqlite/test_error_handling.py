import sys
from pathlib import Path
from Part1_Ch4.sqlite.db_design import create_database
from Part1_Ch4.sqlite.crud_api import CRUDOperations
from Part1_Ch4.sqlite.file_to_db_pipeline import FileToDBPipeline
from Part1_Ch4.sqlite.query_api import SortParams

def main():
    db = create_database("test_errors")
    crud = CRUDOperations(db)
    pipeline = FileToDBPipeline(db)

    errors_caught = 0

    # Test 1: Non-existent document returns None
    if crud.read(999) is None:
        errors_caught += 1

    # Test 2: Delete non-existent document returns False
    if not crud.delete(999):
        errors_caught += 1

    # Test 3: Invalid file path raises FileNotFoundError
    try:
        pipeline.load_file(Path("nonexistent_file.txt"))
    except FileNotFoundError:
        errors_caught += 1

    # Test 4: Invalid sort field raises ValueError
    try:
        SortParams(field="invalid_field")
    except ValueError:
        errors_caught += 1

    if errors_caught == 4:
        print("All error handling tests passed")
        sys.exit(0)
    else:
        print(f"Only {errors_caught}/4 error handling tests passed")
        sys.exit(1)

if __name__ == "__main__":
    main()
