import datetime
from flask_jwt_extended import create_access_token, decode_token
from functools import wraps
from flask import request, jsonify
from backend.models import User
from werkzeug.security import check_password_hash

# Secret key for encoding and decoding JWT tokens (use a secure key in production)
JWT_SECRET_KEY = "your_jwt_secret_key"

def create_jwt_token(user_id):
    """
    Generate JWT token for the user
    :param user_id: The user's ID
    :return: The JWT token
    """
    expiration = datetime.timedelta(hours=1)
    return create_access_token(identity=user_id, expires_delta=expiration, secret=JWT_SECRET_KEY)

def verify_jwt_token(token):
    """
    Verify the JWT token
    :param token: The JWT token
    :return: The decoded payload if valid, otherwise None
    """
    try:
        payload = decode_token(token, key=JWT_SECRET_KEY)
        return payload
    except Exception as e:
        return None

def jwt_required(func):
    """
    Decorator to check if JWT token is present in the request
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"message": "Token is invalid!"}), 401
        
        # Optionally, you can attach the user to the request
        user = User.query.get(payload["sub"])
        if not user:
            return jsonify({"message": "User not found!"}), 401
        
        return func(user, *args, **kwargs)
    
    return decorated_function
