import sys
from Part1_Ch4.sqlite.db_design import create_database
from Part1_Ch4.sqlite.crud_api import CRUDOperations

def main():
    # Create two tenant databases
    db1 = create_database("tenant_test_1")
    db2 = create_database("tenant_test_2")

    crud1 = CRUDOperations(db1)
    crud2 = CRUDOperations(db2)

    # Add data to each tenant
    crud1.create(filename="tenant1.txt", content="Tenant 1 data")
    crud2.create(filename="tenant2.txt", content="Tenant 2 data")

    # Verify isolation
    doc1 = crud1.read(1)
    doc2 = crud2.read(1)

    if (doc1 and doc1['content'] == "Tenant 1 data" and
        doc2 and doc2['content'] == "Tenant 2 data" and
        crud1.count() == 1 and crud2.count() == 1):
        print("Multi-tenancy isolation verified")
        sys.exit(0)
    else:
        print("Multi-tenancy isolation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
