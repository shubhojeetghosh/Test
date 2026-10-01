from sqlalchemy import inspect

from app.database.database import engine


def inspect_database():
    inspector = inspect(engine)

    tables = inspector.get_table_names()

    print("DATABASE SCHEMA")
    print("=" * 60)

    for table in tables:
        print(f"\nTABLE: {table}")
        print("-" * 60)

        columns = inspector.get_columns(table)

        for column in columns:
            print(
                f"  {column['name']} | "
                f"{column['type']} | "
                f"nullable={column['nullable']}"
            )

        primary_key = inspector.get_pk_constraint(table)

        print("\n  PRIMARY KEY:")
        print(f"    {primary_key['constrained_columns']}")

        foreign_keys = inspector.get_foreign_keys(table)

        if foreign_keys:
            print("\n  FOREIGN KEYS:")

            for fk in foreign_keys:
                print(
                    f"    {fk['constrained_columns']} "
                    f"-> {fk['referred_table']}"
                    f"({fk['referred_columns']})"
                )


if __name__ == "__main__":
    inspect_database()