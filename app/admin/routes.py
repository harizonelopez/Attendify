from flask import ( Blueprint, render_template, request, redirect, url_for, flash, session )
from werkzeug.security import generate_password_hash
from app.auth.decorators import role_required
from app.database.db import db, q
from app.services.audit import log_action
from app.services.analytics import course_statistics
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

admin = Blueprint("admin", __name__, url_prefix="/admin")

@admin.route("/")
@role_required("admin")
def dashboard():
    users = q("SELECT * FROM users ORDER BY id DESC")
    courses = q(
        """
        SELECT courses.*, users.full_name AS lecturer_name
        FROM courses
        LEFT JOIN users ON courses.lecturer_id = users.id
        ORDER BY courses.id DESC
        """
    )
    students = q(
        "SELECT * FROM users WHERE role = 'student' ORDER BY full_name"
    )
    lecturers = q(
        "SELECT * FROM users WHERE role = 'lecturer' ORDER BY full_name"
    )

    course_analytics = []
    for course in courses:
        total_students = q(
            """
            SELECT COUNT(*) AS total
            FROM enrollments
            WHERE course_id = ?
            """,
            (course["id"],),
            one=True
        )["total"]

        attendance_records = q(
            """
            SELECT student_id, present
            FROM attendance
            WHERE course_id = ?
            """,
            (course["id"],)
        )

        statistics = course_statistics(
            total_students,
            attendance_records
        )

        course_analytics.append({
            "course": course,
            "statistics": statistics
        })

    return render_template(
        "admin/dashboard.html",
        users=users,
        courses=courses,
        students=students,
        lecturers=lecturers,
        course_analytics=course_analytics
    )


@admin.route("/audit-logs")
@role_required("admin")
def audit_logs():
    # Collect filter values from the URL.
    search = request.args.get("search", "").strip()
    role = request.args.get("role", "").strip()
    action = request.args.get("action", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    filters = {
        "search": search,
        "role": role,
        "action": action,
        "date_from": date_from,
        "date_to": date_to
    }

    conditions = []
    params = []

    # Search across user and activity information.
    if search:
        conditions.append("""
            (
                username LIKE ?
                OR full_name LIKE ?
                OR action LIKE ?
                OR details LIKE ?
            )
        """)
        term = f"%{search}%"
        params.extend([term, term, term, term])

    # Filter by role.
    if role in ("admin", "lecturer", "student"):
        conditions.append("role = ?")
        params.append(role)

    # Filter by action.
    if action:
        conditions.append("action = ?")
        params.append(action)

    # Interpret date filters using Kenya's local timezone.
    nairobi_tz = ZoneInfo("Africa/Nairobi")
    utc_tz = ZoneInfo("UTC")

    try:
        if date_from:
            start_date = date.fromisoformat(date_from)
            start_local = datetime.combine(
                start_date, time.min, tzinfo=nairobi_tz
            )
            start_utc = start_local.astimezone(utc_tz)

            conditions.append("created_at >= ?")
            params.append(
                start_utc.strftime("%Y-%m-%d %H:%M:%S")
            )

        if date_to:
            end_date = date.fromisoformat(date_to) + timedelta(days=1)
            end_local = datetime.combine(
                end_date, time.min, tzinfo=nairobi_tz
            )
            end_utc = end_local.astimezone(utc_tz)

            conditions.append("created_at < ?")
            params.append(
                end_utc.strftime("%Y-%m-%d %H:%M:%S")
            )

    except ValueError:
        pass

    # Build the query using active filters.
    sql = """
        SELECT
            id,
            user_id,
            username,
            full_name,
            role,
            action,
            entity_type,
            entity_id,
            details,
            created_at
        FROM audit_logs
    """

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += """
        ORDER BY created_at DESC, id DESC
        LIMIT 200
    """

    logs = q(sql, tuple(params))

    # Load available actions for the action filter.
    actions = q("""
        SELECT DISTINCT action
        FROM audit_logs
        ORDER BY action ASC
    """)

    # Convert UTC timestamps to Nairobi local time.
    formatted_logs = []

    for log in logs:
        log_data = dict(log)
        utc_time = datetime.fromisoformat(
            log_data["created_at"]
        ).replace(tzinfo=utc_tz)
        log_data["local_time"] = utc_time.astimezone(
            nairobi_tz
        ).strftime("%d %b %Y, %I:%M:%S %p")
        formatted_logs.append(log_data)

    return render_template("admin/audit_logs.html", logs=formatted_logs, filters=filters, actions=actions)


@admin.route("/create-user", methods=["POST"])
@role_required("admin")
def create_user():
    username = request.form.get("username", "").strip()
    full_name = request.form.get("full_name", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "").strip()

    if not username or not full_name or not password:
        flash("All account fields are required.", "danger")
        return redirect(url_for("admin.dashboard"))

    if len(password) < 8:
        flash("Password must contain at least 8 characters.", "warning")
        return redirect(url_for("admin.dashboard"))

    if role not in ("admin", "lecturer", "student"):
        flash("Invalid account role.", "danger")
        return redirect(url_for("admin.dashboard"))

    existing_user = q(
        "SELECT id FROM users WHERE username = ?",
        (username,),
        one=True
    )

    if existing_user:
        flash("That username is already in use.", "warning")
        return redirect(url_for("admin.dashboard"))

    try:
        cursor = db().execute(
            """
            INSERT INTO users (username, full_name, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (username, full_name, generate_password_hash(password), role)
        )

        user_id = cursor.lastrowid
        db().commit()

        log_action(
            action="create_user",
            entity_type="user",
            entity_id=user_id,
            details=f"Created {role} account: {username} ({full_name})."
        )

        flash("Account created successfully.", "success")

    except Exception:
        db().rollback()
        flash("An error occurred while creating the account.", "danger")

    return redirect(url_for("admin.dashboard"))


@admin.route("/create-course", methods=["POST"])
@role_required("admin")
def create_course():
    code = request.form.get("code", "").strip().upper()
    name = request.form.get("name", "").strip()
    lecturer_id = request.form.get("lecturer_id", "").strip()

    if not code or not name or not lecturer_id:
        flash("All course fields are required.", "danger")
        return redirect(url_for("admin.dashboard"))

    if not lecturer_id.isdigit():
        flash("Invalid lecturer selection.", "danger")
        return redirect(url_for("admin.dashboard"))

    lecturer = q(
        "SELECT id FROM users WHERE id = ? AND role = 'lecturer'",
        (int(lecturer_id),),
        one=True
    )

    if not lecturer:
        flash("Please select a valid lecturer.", "danger")
        return redirect(url_for("admin.dashboard"))

    existing_course = q(
        "SELECT id FROM courses WHERE code = ?",
        (code,),
        one=True
    )

    if existing_course:
        flash("A course with that code already exists.", "warning")
        return redirect(url_for("admin.dashboard"))

    try:
        cursor = db().execute(
            """
            INSERT INTO courses (code, name, lecturer_id)
            VALUES (?, ?, ?)
            """,
            (code, name, int(lecturer_id))
        )

        course_id = cursor.lastrowid
        db().commit()

        log_action(
            action="create_course",
            entity_type="course",
            entity_id=course_id,
            details=f"Created course {code}: {name}."
        )

        flash("Course created successfully.", "success")

    except Exception:
        db().rollback()
        flash("An error occurred while creating the course.", "danger")

    return redirect(url_for("admin.dashboard"))


@admin.route("/enroll", methods=["POST"])
@role_required("admin")
def enroll_student():
    student_id = request.form.get("student_id", "").strip()
    course_id = request.form.get("course_id", "").strip()

    if not student_id.isdigit() or not course_id.isdigit():
        flash("Invalid student or course selection.", "danger")
        return redirect(url_for("admin.dashboard"))

    student_id = int(student_id)
    course_id = int(course_id)

    student = q(
        "SELECT id, username, full_name FROM users WHERE id = ? AND role = 'student'",
        (student_id,),
        one=True
    )

    course = q(
        "SELECT id, code, name FROM courses WHERE id = ?",
        (course_id,),
        one=True
    )

    if not student or not course:
        flash("Invalid student or course selection.", "danger")
        return redirect(url_for("admin.dashboard"))

    existing_enrollment = q(
        """
        SELECT student_id FROM enrollments
        WHERE student_id = ? AND course_id = ?
        """,
        (student_id, course_id),
        one=True
    )

    if existing_enrollment:
        flash("Student already enrolled in the course.", "warning")
        return redirect(url_for("admin.dashboard"))

    try:
        db().execute(
            """
            INSERT INTO enrollments (student_id, course_id)
            VALUES (?, ?)
            """,
            (student_id, course_id)
        )

        db().commit()

        log_action(
            action="enroll_student",
            entity_type="enrollment",
            entity_id=course_id,
            details=f"Enrolled {student['full_name']} ({student['username']}) in {course['code']}."
        )

        flash("Student enrolled successfully.", "success")

    except Exception:
        db().rollback()
        flash("An error occurred while enrolling the student.", "danger")

    return redirect(url_for("admin.dashboard"))


# Delete a lecturer, student or administrator account
@admin.route("/delete-user/<int:user_id>", methods=["POST"])
@role_required("admin")
def delete_user(user_id):
    connection = db()
    user = q(
        "SELECT id, username, full_name, role FROM users WHERE id = ?",
        (user_id,),
        one=True
    )

    if not user:
        flash("Account not found.", "warning")
        return redirect(url_for("admin.dashboard"))

    # Prevent an administrator from deleting their own account.
    if user["id"] == session["user_id"]:
        flash("Current session admin account can't be deleted.", "danger")
        return redirect(url_for("admin.dashboard"))

    # Prevent deletion of the last administrator.
    if user["role"] == "admin":
        admin_count = q(
            "SELECT COUNT(*) AS total FROM users WHERE role = 'admin'",
            one=True
        )["total"]

        if admin_count <= 1:
            flash("Admin account can't be deleted.", "danger")
            return redirect(url_for("admin.dashboard"))

    # A lecturer must have their courses reassigned or deleted first.
    if user["role"] == "lecturer":
        assigned_courses = q(
            "SELECT id FROM courses WHERE lecturer_id = ?",
            (user_id,)
        )

        if assigned_courses:
            flash("The lecturer still has assigned courses. Reassign or delete those courses first.", "warning")
            return redirect(url_for("admin.dashboard"))

    try:
        if user["role"] == "student":
            connection.execute(
                "DELETE FROM attendance WHERE student_id = ?",
                (user_id,)
            )

            connection.execute(
                "DELETE FROM enrollments WHERE student_id = ?",
                (user_id,)
            )

        connection.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )

        connection.commit()

        log_action(
            action="delete_user",
            entity_type="user",
            entity_id=user_id,
            details=f"Deleted {user['role']} account: {user['username']} ({user['full_name']})."
        )

        flash(
            f"Account for {user['full_name']} deleted successfully.",
            "success"
        )

    except Exception:
        connection.rollback()
        flash("Unable to delete this account.", "danger")

    return redirect(url_for("admin.dashboard"))


# Delete a course
@admin.route("/delete-course/<int:course_id>", methods=["POST"])
@role_required("admin")
def delete_course(course_id):
    connection = db()

    course = q(
        "SELECT id, code, name FROM courses WHERE id = ?",
        (course_id,),
        one=True
    )

    if not course:
        flash("Course not found.", "warning")
        return redirect(url_for("admin.dashboard"))

    try:
        # Remove attendance records associated with this course.
        connection.execute(
            "DELETE FROM attendance WHERE course_id = ?",
            (course_id,)
        )

        # Remove student enrollments associated with this course.
        connection.execute(
            "DELETE FROM enrollments WHERE course_id = ?",
            (course_id,)
        )

        # Finally, remove the course.
        connection.execute(
            "DELETE FROM courses WHERE id = ?",
            (course_id,)
        )

        connection.commit()

        log_action(
            action="delete_course",
            entity_type="course",
            entity_id=course_id,
            details=f"Deleted course {course['code']}: {course['name']}."
        )

        flash(
            f"Course {course['code']} deleted successfully.",
            "success"
        )

    except Exception:
        connection.rollback()
        flash("Unable to delete this course.", "danger")

    return redirect(url_for("admin.dashboard"))
