from functools import wraps

from flask import flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User


def hash_password(password):
    return generate_password_hash(password)


def verify_password(user, password):
    return bool(user and user.is_active and check_password_hash(user.password_hash, password))


def current_user():
    user_id = session.get("admin_user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def current_volunteer():
    volunteer_id = session.get("volunteer_user_id")
    if not volunteer_id:
        return None
    return User.query.get(volunteer_id)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user.role not in {"admin", "editor"}:
            flash("Please log in to continue.")
            return redirect(url_for("main.admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                flash("Please log in to continue.")
                return redirect(url_for("main.admin_login", next=request.path))
            if user.role not in roles:
                flash("You do not have permission to access that area.")
                return redirect(url_for("main.admin_dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def volunteer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        volunteer = current_volunteer()
        if not volunteer or volunteer.role != "volunteer":
            flash("Please log in to continue.")
            return redirect(url_for("main.volunteer_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
