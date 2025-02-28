from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from backend.database import db, initialize_database
from backend.routes import api_routes
from backend.utils.logger import configure_logger
from backend.config import Config

# Initialize the app
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

    return app

if __name__ == "__main__":
    # Create and run the app
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
