from flask import session
from app.database.db import db

def log_action(
    action,
    entity_type = None,
    entity_id = None,
    details = None
):

    """Record an authenticated user's activity."""

    connection = db()
    connection.execute(
        """
        INSERT INTO audit_logs (
            user_id,
            username,
            full_name,
            role,
            action,
            entity_type,
            entity_id,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session.get("user_id"),
            session.get("username"),
            session.get("full_name"),
            session.get("role"),
            action,
            entity_type,
            entity_id,
            details
        )
    )

    connection.commit()