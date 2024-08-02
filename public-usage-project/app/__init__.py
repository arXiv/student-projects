from flask import Flask
from config import config
from app.api import api
import multiprocessing
from flask_cors import CORS
from datetime import datetime
from app import download_data


def create_app(app_config='development'):
    app = Flask(__name__)

    # Apply CORS

    CORS(app)

    # Apply config
    app.config.from_object(config[app_config])

    # Register blueprints
    from app.main.routes import main
    app.register_blueprint(main)

    app.register_blueprint(api, url_prefix='/api')

    return app
