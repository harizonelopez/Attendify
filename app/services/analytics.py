from app.config import Config

def analyse(attended, total_sessions):
    """Calculate attendance percentage and projected performance."""
    if total_sessions == 0:
        return {
            "percentage": 0,
            "status": "No attendance data",
            "risk": "Unknown",
            "projected_percentage": 0
        }

    percentage = (attended / total_sessions) * 100
    remaining_sessions = max(
        Config.SEMESTER_SESSIONS - total_sessions,
        0
    )

    projected_attendance = (
        attended + (percentage / 100 * remaining_sessions)
    )

    projected_percentage = (
        projected_attendance / Config.SEMESTER_SESSIONS
    ) * 100

    status = (
        "Good Standing"
        if percentage >= Config.THRESHOLD
        else "Below Attendance Threshold"
    )

    risk = (
        "Low"
        if projected_percentage >= Config.THRESHOLD
        else "High"
    )

    return {
        "percentage": round(percentage, 2),
        "status": status,
        "risk": risk,
        "projected_percentage": round(projected_percentage, 2)
    }


def course_statistics(total_students, attendance_records):
    """Calculate overall attendance statistics for a course."""
    if total_students == 0 or not attendance_records:
        return {
            "total_students": total_students,
            "total_sessions": 0,
            "average_attendance": 0,
            "at_risk_students": 0,
            "good_standing_students": 0
        }

    student_attendance = {}
    for record in attendance_records:
        student_id = record["student_id"]
        if student_id not in student_attendance:
            student_attendance[student_id] = {
                "attended": 0,
                "sessions": 0
            }

        student_attendance[student_id]["sessions"] += 1
        if record["present"]:
            student_attendance[student_id]["attended"] += 1

    percentages = []
    at_risk = 0
    good_standing = 0

    for data in student_attendance.values():
        result = analyse(
            data["attended"],
            data["sessions"]
        )

        percentages.append(result["percentage"])

        if result["risk"] == "High":
            at_risk += 1
        else:
            good_standing += 1

    average = sum(percentages) / len(percentages)

    total_sessions = max(
        data["sessions"]
        for data in student_attendance.values()
    )

    return {
        "total_students": total_students,
        "total_sessions": total_sessions,
        "average_attendance": round(average, 2),
        "at_risk_students": at_risk,
        "good_standing_students": good_standing
    }
