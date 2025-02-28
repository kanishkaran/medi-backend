from os import environ, makedirs, path, getcwd
from os.path import exists

class Config:
    # Flask settings
    SECRET_KEY = environ.get("SECRET_KEY", "supersecretkey")
    DEBUG = environ.get("FLASK_DEBUG", True)

    # Database configuration
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{path.join(getcwd(), 'Medicines.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = environ.get("JWT_SECRET_KEY", "jwtsecretkey")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # Other configurations
    UPLOAD_FOLDER = environ.get("UPLOAD_FOLDER", "backend/uploads")
    if not exists(UPLOAD_FOLDER):
        makedirs(UPLOAD_FOLDER)
