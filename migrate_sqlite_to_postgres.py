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
        with psycopg.connect(database_url) as destination:
            # Refuse to import into a database containing records.
            for table in TABLES:
                count = destination.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

                if count != 0:
                    raise RuntimeError(
                        f"Destination table '{table}' is not empty. "
                        "Migration stopped to prevent duplicate records."
                    )

            print("Destination verified: all tables are empty.")

            # Transfer records while preserving original IDs.
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

                print(f"{table}: {len(rows)} records transferred.")

            # Reset identity sequences for tables with generated IDs.
            for table in ("users", "courses", "audit_logs"):
                destination.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        (SELECT MAX(id) FROM {table}),
                        true
                    )
                    WHERE EXISTS (SELECT 1 FROM {table})
                    """
                )
        print("\nMigration completed successfully.")
    finally:
        source.close()

if __name__ == "__main__":
    main()
