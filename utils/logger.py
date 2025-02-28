import logging
from logging.handlers import RotatingFileHandler
import os

def configure_logger(app):
    """
    Configures logging for the Flask application.
    Supports console logging, file logging, and log rotation.
    """
    # Create a directory for logs if it doesn't exist
    log_directory = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Define log file path
    log_file = os.path.join(log_directory, "app.log")

    # Log format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] - %(message)s"
    )

    # Console handler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Rotating file handler for logging to a file with rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )  # 10 MB per file, 5 backups
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Set up Flask's logger to use the configured handlers
    app.logger.setLevel(logging.INFO)
    app.logger.handlers = []  # Clear default handlers
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    # Test the logger
    app.logger.info("Logger has been configured successfully.")
