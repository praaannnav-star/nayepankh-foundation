from app import create_app, db
from app.services.admin_seed import ensure_default_admin
from app.services.content_seed import upsert_curated_content
from app.services.content_importer import import_all


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = import_all()
        upsert_curated_content()
        admin, created = ensure_default_admin()
        summary["admin_user"] = admin.email
        summary["admin_user_created"] = created
        db.session.commit()
        return summary


if __name__ == "__main__":
    result = seed()
    print("Seed complete")
    for key, value in result.items():
        print(f"{key}: {value}")
