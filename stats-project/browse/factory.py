from flask import Flask
from config import config
from browse.api import api

from flask_cors import CORS

def create_app(app_config='development'):
    app = Flask(__name__)

    # Apply CORS
    CORS(app)

    # Apply config
    #app.config.from_object(config[app_config])

    # Register blueprints
    from browse.routes.ui import main
    app.register_blueprint(main)

    app.register_blueprint(api, url_prefix='/api')

    return app
