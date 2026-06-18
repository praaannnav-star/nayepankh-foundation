import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "instance", "nayepankh.db")
DATABASE_URL = os.environ.get("DATABASE_URL") or DEFAULT_DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_ROOT = os.path.join(BASE_DIR, "static", "uploads")
    SOURCE_SITE_URL = os.environ.get("SOURCE_SITE_URL", "https://nayepankh.com")
