from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_dance.contrib.google import make_google_blueprint
from .database import db, initialize_database
from .routes import api_routes
from .utils.logger import configure_logger
from .config import Config

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize logger
    configure_logger(app)

    # Enable CORS
    CORS(app)

    # Initialize JWT
    jwt = JWTManager(app)

    # Initialize database
    initialize_database(app)

    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(api_routes)

    # Google OAuth Blueprint
    google_bp = make_google_blueprint(
        client_id="1075856046253-71vvtot48lv4p82cloon1145ovf123ga.apps.googleusercontent.com",
        client_secret="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",
        redirect_to="google_login_callback"
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)