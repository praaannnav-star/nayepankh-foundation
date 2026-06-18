import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.services.admin_seed import ensure_default_admin


app = create_app()


with app.app_context():
    db.create_all()
    admin, created = ensure_default_admin()
    print("Database initialized.")
    print(f"Admin user: {admin.email} ({'created' if created else 'exists'})")
