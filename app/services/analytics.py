from app.config import Config

def analyse(attended, total_sessions):
    # Handle courses without recorded attendance
    if total_sessions == 0:
        return {
            "percentage": 0,
            "status": "No attendance data",
            "risk": "Unknown",
            "projected_percentage": 0
        }

    # Calculate current attendance percentage
    percentage = (attended / total_sessions) * 100

    # Determine remaining semester sessions
    remaining_sessions = max(
        Config.SEMESTER_SESSIONS - total_sessions,
        0
    )

    # Estimate future attendance using the current attendance rate
    projected_attendance = (
        attended + (percentage / 100 * remaining_sessions)
    )

    projected_percentage = (
        projected_attendance / Config.SEMESTER_SESSIONS
    ) * 100

    # Determine current academic standing
    status = (
        "Good Standing"
        if percentage >= Config.THRESHOLD
        else "Below Attendance Threshold"
    )

    # Estimate attendance risk
    if projected_percentage >= Config.THRESHOLD:
        risk = "Low"
    else:
        risk = "High"

    return {
        "percentage": round(percentage, 2),
        "status": status,
        "risk": risk,
        "projected_percentage": round(projected_percentage, 2)
    }