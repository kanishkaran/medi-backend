from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance
db = SQLAlchemy()

def initialize_database(app):
    """
    Initializes the database by binding it to the Flask app.
    Does not overwrite existing tables in Medicines.db.
    """
    # Bind the app to SQLAlchemy
    db.init_app(app)

    # Ensure that changes only occur in the app context
    with app.app_context():
        # Create all tables except the pre-existing ones in Medicines.db
        try:
            db.create_all()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"Database initialization failed: {e}")
