import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from app.services.admin_seed import ensure_default_admin
from app.services.content_seed import upsert_curated_content


app = create_app()


with app.app_context():
    db.create_all()
    upsert_curated_content()
    admin, created = ensure_default_admin()
    print("Database tables ensured.")
    print(f"Admin user: {admin.email} ({'created' if created else 'exists'})")
