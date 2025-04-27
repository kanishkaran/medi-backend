from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_dance.contrib.google import make_google_blueprint
from .database import db, initialize_database
from .routes import api_routes
from .utils.logger import configure_logger
from .config import Config
import os

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize logger
    configure_logger(app)

    # Enable CORS with the specific domain
    CORS(app, resources={r"/*": {"origins": "https://mediverse.netlify.app"}})

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
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        redirect_to="google_login_callback"
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    return app

if __name__ == "__main__":
    app = create_app()
    port = os.getenv("PORT", 5000)
    app.run(host="0.0.0.0", port=int(port), debug=False)
