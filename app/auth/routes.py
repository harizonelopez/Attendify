from flask import (Blueprint, render_template, request, redirect, url_for, session, flash)
from werkzeug.security import check_password_hash
from app.database.db import q

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

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin.dashboard"))

            elif user["role"] == "lecturer":
                return redirect(url_for("lecturer.dashboard"))

            return redirect(url_for("student.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    
    return redirect(url_for("auth.login"))