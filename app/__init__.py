import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../static")
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_ROOT"], exist_ok=True)

    db.init_app(app)

    from app.routes import bp

    app.register_blueprint(bp)
    return app
