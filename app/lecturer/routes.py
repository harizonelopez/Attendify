import csv
import io
from datetime import date
from flask import (Blueprint, render_template, request, redirect, url_for, flash, session, Response, current_app)
from app.auth.decorators import role_required
from app.database.db import db, q
from app.services.audit import log_action

lecturer = Blueprint("lecturer", __name__, url_prefix="/lecturer")

@lecturer.route("/")
@role_required("lecturer")
def dashboard():
    lecturer_id = session["user_id"]
    courses = q(
        """
        SELECT
            courses.*,
            COUNT(enrollments.student_id) AS student_count
        FROM courses
        LEFT JOIN enrollments
            ON courses.id = enrollments.course_id
        WHERE courses.lecturer_id = ?
        GROUP BY courses.id
        ORDER BY courses.code
        """,
        (lecturer_id,)
    )

    return render_template("lecturer/dashboard.html", courses=courses)


@lecturer.route("/mark/<int:cid>", methods=["GET", "POST"])
@role_required("lecturer")
def mark_attendance(cid):
    course = q(
        """
        SELECT * FROM courses
        WHERE id = ? AND lecturer_id = ?
        """,
        (cid, session["user_id"]),
        one=True
    )

    if not course:
        flash("Access denied.", "danger")
        return redirect(url_for("lecturer.dashboard"))

    students = q(
        """
        SELECT users.id, users.full_name, users.username
        FROM enrollments
        JOIN users ON enrollments.student_id = users.id
        WHERE enrollments.course_id = ?
        ORDER BY users.full_name
        """,
        (cid,)
    )

    today = date.today().isoformat()

    if request.method == "POST":
        attendance_date = request.form.get("date", "").strip()
        # Validate attendance date
        try:
            date.fromisoformat(attendance_date)
        except ValueError:
            flash("Valid date required .", "danger")
            return redirect(
                url_for("lecturer.mark_attendance", cid=cid)
            )

        # Ensure every student has an explicit selection
        for student in students:
            selection = request.form.get(
                f"student_{student['id']}"
            )

            if selection not in ("present", "absent"):
                flash("Mark every student as either present or absent.", "warning")
                return redirect(
                    url_for("lecturer.mark_attendance", cid=cid)
                )

        connection = db()
        present_count = 0
        absent_count = 0

        try:
            for student in students:
                present = (
                    1 if request.form.get(
                        f"student_{student['id']}"
                    ) == "present" else 0
                )

                if present:
                    present_count += 1
                else:
                    absent_count += 1

                connection.execute(
                    """
                    INSERT INTO attendance
                        (course_id, student_id, date, present)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(course_id, student_id, date)
                    DO UPDATE SET present = excluded.present
                    """,
                    (cid, student["id"], attendance_date, present)
                )

            connection.commit()

        except Exception:
            connection.rollback()
            flash("An error occurred while saving the attendance.", "danger")

        else:
            # Record the successful attendance operation
            try:
                log_action(
                    action="mark_attendance",
                    entity_type="attendance_session",
                    entity_id=cid,
                    details=(
                        f"Attendance recorded for {course['code']} "
                        f"on {attendance_date}. "
                        f"Present: {present_count}, "
                        f"Absent: {absent_count}."
                    )
                )

                flash("Attendance successfully saved.", "success")

            except Exception:
                current_app.logger.exception("Failed to record attendance audit log.")
                flash("Attendance was saved, but its audit record couldn't be created.", "warning")

        return redirect(
            url_for("lecturer.mark_attendance", cid=cid)
        )

    return render_template(
        "lecturer/mark_attendance.html",
        course=course,
        students=students,
        today=today
    )


@lecturer.route("/report/<int:cid>")
@role_required("lecturer")
def report(cid):
    course = q(
        """
        SELECT * FROM courses
        WHERE id = ? AND lecturer_id = ?
        """,
        (cid, session["user_id"]),
        one=True
    )

    if not course:
        flash("Access denied.", "danger")
        return redirect(url_for("lecturer.dashboard"))

    reports = q(
        """
        SELECT
            users.id,
            users.full_name,
            users.username,
            COUNT(attendance.date) AS total,
            COALESCE(SUM(attendance.present), 0) AS attended,
            CASE
                WHEN COUNT(attendance.date) = 0 THEN 0
                ELSE ROUND(
                    SUM(attendance.present) * 100.0 /
                    COUNT(attendance.date), 2
                )
            END AS percentage
        FROM enrollments
        JOIN users
            ON enrollments.student_id = users.id
        LEFT JOIN attendance
            ON attendance.student_id = users.id
            AND attendance.course_id = enrollments.course_id
        WHERE enrollments.course_id = ?
        GROUP BY users.id
        ORDER BY users.full_name
        """,
        (cid,)
    )

    total_sessions = q(
        """
        SELECT COUNT(DISTINCT date) AS total
        FROM attendance
        WHERE course_id = ?
        """,
        (cid,),
        one=True
    )["total"]

    return render_template(
        "lecturer/report.html",
        course=course,
        reports=reports,
        total_sessions=total_sessions
    )


@lecturer.route("/export/<int:cid>", endpoint="export")
@role_required("lecturer")
def export_attendance(cid):
    course = q(
        """
        SELECT * FROM courses
        WHERE id = ? AND lecturer_id = ?
        """,
        (cid, session["user_id"]),
        one=True
    )

    if not course:
        flash("Access denied.", "danger")
        return redirect(url_for("lecturer.dashboard"))

    records = q(
        """
        SELECT
            users.full_name,
            users.username,
            attendance.date,
            attendance.present
        FROM attendance
        JOIN users
            ON attendance.student_id = users.id
        WHERE attendance.course_id = ?
        ORDER BY attendance.date, users.full_name
        """,
        (cid,)
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Student Name",
        "Username",
        "Date",
        "Status"
    ])

    for record in records:
        writer.writerow([
            record["full_name"],
            record["username"],
            record["date"],
            "Present" if record["present"] else "Absent"
        ])

    # Record successful report export
    try:
        log_action(
            action="export_report",
            entity_type="course",
            entity_id=cid,
            details=(
                f"Exported attendance report for "
                f"{course['code']}. Records: {len(records)}."
            )
        )
    except Exception:
        current_app.logger.exception(
            "Failed to record report export audit log."
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename={course['code']}_attendance.csv"
        }
    )
