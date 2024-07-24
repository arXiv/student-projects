from flask import Flask
from config import config
from app.api import api

def create_app(app_config='development'):
    app = Flask(__name__)

    # apply config 
    app.config.from_object(config[app_config])

    # register blueprints
    from app.main.routes import main
    app.register_blueprint(main)

    app.register_blueprint(api, url_prefix='/api')

    return app