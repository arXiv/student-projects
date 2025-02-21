from flask import Flask
from config import config
from browse.api import api
from browse.routes.graph_routes import graph_routes
from flask_cors import CORS


def create_app(app_config="development"):
    app = Flask(__name__)

    # Apply CORS
    CORS(app)


    # Register blueprints
    app.register_blueprint(graph_routes) # the front end, in other words
    app.register_blueprint(api, url_prefix="/api") # the back end, in other words

    return app
