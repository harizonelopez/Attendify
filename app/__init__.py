import os
from flask import Flask, session, redirect, url_for
from app.config import Config
from app.database.db import close_db, init_db

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load application configuration
    app.config.from_object(Config)

    # Ensure the instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Database lifecycle
    app.teardown_appcontext(close_db)

    # Initialize database
    with app.app_context():
        init_db()

    # Register application blueprints
    from app.auth.routes import auth
    from app.admin.routes import admin
    from app.lecturer.routes import lecturer
    from app.student.routes import student

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(lecturer)
    app.register_blueprint(student)

    # Application home route
    @app.route("/")
    def index():
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        
        role = session.get("role")

        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif role == "lecturer":
            return redirect(url_for("lecturer.dashboard"))
        elif role == "student":
            return redirect(url_for("student.dashboard"))

        session.clear()
        return redirect(url_for("auth.login"))

    return app