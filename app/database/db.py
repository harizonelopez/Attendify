import sqlite3
from datetime import date, timedelta
from flask import g, current_app
from werkzeug.security import generate_password_hash

def db():
    """Get one SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"]
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def q(sql, args=(), one=False):
    """Execute a SELECT query."""
    rows = db().execute(sql, args).fetchall()
    if one:
        return rows[0] if rows else None
    return rows


def run(sql, args=()):
    """Execute INSERT, UPDATE or DELETE queries."""
    connection = db()
    connection.execute(sql, args)
    connection.commit()


def close_db(error=None):
    """Close the database connection after each request."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    """Create database tables and insert initial demo data."""
    connection = sqlite3.connect(
        current_app.config["DATABASE"]
    )
    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                full_name TEXT,
                password_hash TEXT,
                role TEXT
            );
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY,
                code TEXT,
                name TEXT,
                lecturer_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS enrollments (
                student_id INTEGER,
                course_id INTEGER,
                UNIQUE(student_id, course_id)
            );
            CREATE TABLE IF NOT EXISTS attendance (
                course_id INTEGER,
                student_id INTEGER,
                date TEXT,
                present INTEGER,
                UNIQUE(course_id, student_id, date)
            );
        """)

        # Seed demo accounts only when the database is empty.
        if not connection.execute(
            "SELECT 1 FROM users LIMIT 1"
        ).fetchone():
            def add_user(username, full_name, password, role):
                cursor = connection.execute(
                    """
                    INSERT INTO users
                    (username, full_name, password_hash, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        username,
                        full_name,
                        generate_password_hash(password),
                        role
                    )
                )
                return cursor.lastrowid

            admin_id = add_user(
                "admin",
                "System Admin",
                "admin123",
                "admin"
            )
            lecturer_id = add_user(
                "lecturer1",
                "Dr. Wanjiru",
                "lecturer123",
                "lecturer"
            )
            student1_id = add_user(
                "student1",
                "Brian Kamau",
                "student123",
                "student"
            )
            student2_id = add_user(
                "student2",
                "Grace Njeri",
                "student123",
                "student"
            )

            # Create a demonstration course.
            cursor = connection.execute(
                """
                INSERT INTO courses (code, name, lecturer_id)
                VALUES (?, ?, ?)
                """,
                (
                    "CS101",
                    "Intro to Programming",
                    lecturer_id
                )
            )
            course_id = cursor.lastrowid

            # Enroll demonstration students.
            connection.executemany(
                """
                INSERT INTO enrollments
                (student_id, course_id)
                VALUES (?, ?)
                """,
                [
                    (student1_id, course_id),
                    (student2_id, course_id)
                ]
            )

            # Generate eight sample attendance sessions.
            student1 = [1, 1, 1, 0, 1, 0, 0, 0]
            student2 = [1, 1, 1, 1, 1, 1, 0, 1]
            start = date.today() - timedelta(weeks=8)
            for i in range(8):
                attendance_date = (
                    start + timedelta(weeks=i)
                ).isoformat()
                connection.execute(
                    """
                    INSERT INTO attendance
                    (course_id, student_id, date, present)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        course_id,
                        student1_id,
                        attendance_date,
                        student1[i]
                    )
                )
                connection.execute(
                    """
                    INSERT INTO attendance
                    (course_id, student_id, date, present)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        course_id,
                        student2_id,
                        attendance_date,
                        student2[i]
                    )
                )
        connection.commit()
    finally:
        connection.close()

        