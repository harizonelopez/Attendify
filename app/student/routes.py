from flask import Blueprint, render_template, session, current_app
from app.auth.decorators import role_required
from app.database.db import q
from app.services.analytics import analyse


student = Blueprint("student", __name__, url_prefix="/student")

@student.route("/")
@role_required("student")
def dashboard():
    student_id = session["user_id"]
    courses = q(
        """
        SELECT
            courses.id,
            courses.code,
            courses.name,
            users.full_name AS lecturer_name,
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
        JOIN courses
            ON enrollments.course_id = courses.id
        LEFT JOIN users
            ON courses.lecturer_id = users.id
        LEFT JOIN attendance
            ON attendance.course_id = courses.id
            AND attendance.student_id = enrollments.student_id
        WHERE enrollments.student_id = ?
        GROUP BY courses.id
        ORDER BY courses.code
        """,
        (student_id,)
    )
    course_data = []

    for course in courses:
        course_item = dict(course)
        course_item["risk_analysis"] = analyse(
            course_item["attended"],
            course_item["total"]
        )

        course_data.append(course_item)

    history = q(
        """
        SELECT
            courses.code AS course_code,
            courses.name AS course_name,
            attendance.date,
            attendance.present
        FROM attendance
        JOIN courses
            ON attendance.course_id = courses.id
        WHERE attendance.student_id = ?
        ORDER BY attendance.date DESC
        """,
        (student_id,)
    )
    threshold = current_app.config["THRESHOLD"]

    return render_template(
        "student/dashboard.html",
        courses=course_data,
        history=history,
        threshold=threshold
    )
