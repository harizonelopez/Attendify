from flask import ( Blueprint, render_template, request, redirect, url_for, session, flash )
from werkzeug.security import check_password_hash, generate_password_hash
from app.database.db import q, run
from app.services.audit import log_action
from app.auth.decorators import role_required

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    # Redirect users who are already authenticated
    if session.get("user_id") and request.method == "GET":
        role = session.get("role")

        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif role == "lecturer":
            return redirect(url_for("lecturer.dashboard"))
        elif role == "student":
            return redirect(url_for("student.dashboard"))

        session.clear()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = q(
            "SELECT * FROM users WHERE username = ?",
            (username,),
            one=True
        )

        if user and check_password_hash(
            user["password_hash"], password
        ):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            # Record successful login
            log_action(
                action="login",
                entity_type="user",
                entity_id=user["id"],
                details="User sign in successfully."
            )

            if user["role"] == "admin":
                return redirect(url_for("admin.dashboard"))

            elif user["role"] == "lecturer":
                return redirect(url_for("lecturer.dashboard"))

            return redirect(url_for("student.dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth.route("/logout", methods=["POST"])
def logout():
    # Record logout before clearing the session
    log_action(
        action="logout",
        entity_type="user",
        entity_id=session.get("user_id"),
        details="User logged out."
    )
    session.clear()
    flash("You have been successfully signed out.", "success")

    return redirect(url_for("auth.login"))


@auth.route("/change-password", methods=["GET", "POST"])
@role_required("admin", "lecturer", "student")
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        user = q(
            "SELECT * FROM users WHERE id = ?",
            (session["user_id"],),
            one=True
        )

        if not check_password_hash(
            user["password_hash"], current_password
        ):
            flash("Your current password is incorrect.", "danger")
            return redirect(url_for("auth.change_password"))

        if len(new_password) < 8 or not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
            flash("Password criteria not met", "danger")
            return redirect(url_for("auth.change_password"))

        if new_password != confirm_password:
            flash("The new password doesn't match", "danger")
            return redirect(url_for("auth.change_password"))

        if new_password == current_password:
            flash("The new password must be different from your current password", "warning")
            return redirect(url_for("auth.change_password"))

        run(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                generate_password_hash(new_password),
                session["user_id"]
            )
        )

        log_action(
            action="change_password",
            entity_type="user",
            entity_id=session["user_id"],
            details="User changed their password."
        )

        flash("Password successfully changed", "success")
        return redirect(url_for("auth.change_password"))

    return render_template("change_password.html")
