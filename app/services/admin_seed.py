import os

from app import db
from app.auth import hash_password
from app.models import User


DEFAULT_ADMIN_EMAIL = "admin@nayepankh.local"
DEFAULT_ADMIN_PASSWORD = "ChangeMe123!"


def ensure_default_admin():
    email = os.environ.get("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL).strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    name = os.environ.get("ADMIN_NAME", "NayePankh Admin")

    user = User.query.filter_by(email=email).first()
    if user:
        # Render environment variables are the source of truth for the
        # deployment administrator. Synchronize them on startup so a lost or
        # changed password can be recovered without editing the database.
        if os.environ.get("ADMIN_EMAIL") and os.environ.get("ADMIN_PASSWORD"):
            user.name = name
            user.password_hash = hash_password(password)
            user.role = "admin"
            user.is_active = True
            db.session.commit()
        return user, False

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="admin",
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user, True
