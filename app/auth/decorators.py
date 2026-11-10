from functools import wraps
from flask import session, redirect, url_for, abort, request

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(
                url_for("auth.login", next=request.path)
            )
        return view(*args, **kwargs)
    return wrapped_view

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(
                    url_for("auth.login", next=request.path)
                )
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped_view
    return decorator