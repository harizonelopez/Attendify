import os
import sqlite3
import psycopg

SQLITE_DB = "/app/instance/attendance.db"

TABLES = {
    "users": [
        "id", "username", "full_name", "password_hash", "role"
    ],
    "courses": [
        "id", "code", "name", "lecturer_id"
    ],
    "enrollments": [
        "student_id", "course_id"
    ],
    "attendance": [
        "course_id", "student_id", "date", "present"
    ],
    "audit_logs": [
        "id", "user_id", "username", "full_name", "role",
        "action", "entity_type", "entity_id", "details", "created_at"
    ],
}

IDENTITY_TABLES = ("users", "courses", "audit_logs")

def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing.")
    if not os.path.isfile(SQLITE_DB):
        raise FileNotFoundError(SQLITE_DB)

    source = sqlite3.connect(
        f"file:{SQLITE_DB}?mode=ro",
        uri=True
    )

    try:
        # Read and count the original records.
        source_counts = {}
        for table in TABLES:
            source_counts[table] = source.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
        print("Source records:")
        for table, count in source_counts.items():
            print(f"{table}: {count}")

        # Everything inside this context is one transaction.
        with psycopg.connect(database_url) as destination:
            # Safety check: never import into populated tables.
            for table in TABLES:
                count = destination.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                if count != 0:
                    raise RuntimeError(
                        f"Destination table '{table}' contains "
                        f"{count} records. Migration cancelled."
                    )
            print("\nDestination verified: all tables are empty.")

            # Transfer all records, preserving original IDs.
            for table, columns in TABLES.items():
                column_list = ", ".join(columns)
                placeholders = ", ".join(
                    ["%s"] * len(columns)
                )

                rows = source.execute(
                    f"SELECT {column_list} FROM {table}"
                ).fetchall()

                if rows:
                    with destination.cursor() as cursor:
                        cursor.executemany(
                            f"""
                            INSERT INTO {table} ({column_list})
                            VALUES ({placeholders})
                            """,
                            rows
                        )

                print(f"{table}: {len(rows)} records copied.")
            # Verify every table before the transaction commits.
            print("\nVerifying transferred records:")

            for table, expected in source_counts.items():
                actual = destination.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

                print(f"{table}: {actual} / {expected}")

                if actual != expected:
                    raise RuntimeError(
                        f"Count mismatch in {table}. "
                        "The transaction will be rolled back."
                    )

            # Reset generated ID sequences to the imported maximum IDs.
            for table in IDENTITY_TABLES:
                maximum = destination.execute(
                    f"SELECT MAX(id) FROM {table}"
                ).fetchone()[0]

                if maximum is not None:
                    destination.execute(
                        """
                        SELECT setval(
                            pg_get_serial_sequence(%s, %s),
                            %s,
                            true
                        )
                        """,
                        (table, "id", maximum)
                    )

            print("\nAll records verified.")
            print("Identity sequences reset.")
        # Reaching here means the transaction committed successfully.
        print("\nMigration completed successfully.")
    finally:
        source.close()

if __name__ == "__main__":
    main()
