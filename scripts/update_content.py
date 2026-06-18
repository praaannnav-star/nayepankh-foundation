import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.services.content_seed import upsert_curated_content


app = create_app()


with app.app_context():
    upsert_curated_content()
    print("Curated CMS content updated.")
