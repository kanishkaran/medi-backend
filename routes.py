from flask import Blueprint, jsonify, request
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database import db
from models import User, Medicine, Cart, Order, OrderItem
from chatbot.order_management import view_order_history, process_payment, fetch_cart, initiate_checkout, cancel_order
from chatbot.conversation_flow import ConversationFlow
from datetime import datetime

# Blueprint for API routes
api_routes = Blueprint("api_routes", __name__)

 #Google Login Route
@api_routes.route("/login/google", methods=["POST"])
def google_login():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"message": "Token is required"}), 400

    try:
        # Verify the token with Google's servers
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), "1075856046253-71vvtot48lv4p82cloon1145ovf123ga.apps.googleusercontent.com")

        # Extract user information
        email = idinfo["email"]
        username = idinfo.get("name", email.split("@")[0])

        # Check if the user already exists
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create a new user if not already registered
            user = User(
                username=username,
                email=email,
                password=None,  # No password for Google login
                date_of_birth=None,  # Optional
                phone_number=None  # Optional
            )
            db.session.add(user)
            db.session.commit()

        # Generate JWT token
        access_token = create_access_token(identity=user.id)

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "username": user.username,
                "email": user.email
            }
        }), 200

    except ValueError as e:
        return jsonify({"message": "Invalid token", "error": str(e)}), 400
    
# User Registration
@api_routes.route("/register", methods=["POST"])
def register_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    date_of_birth_str = data.get("date_of_birth")
    phone_number = data.get("phone_number")

    # Validations
    if not username or len(username) < 3:
        return jsonify({"message": "Username must be at least 3 characters long."}), 400

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"message": "Invalid email format."}), 400

    if not password or len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters long."}), 400

    if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
        return jsonify({"message": "Phone number must be a 10-digit numeric value."}), 400

    # Convert date_of_birth string to a datetime.date object
    try:
        date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Check if the user is at least 18 years old
    today = datetime.today().date()
    if (today.year - date_of_birth.year) - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day)) < 18:
        return jsonify({"message": "You must be at least 18 years old to register."}), 400

    # Check for existing email or phone number
    if User.query.filter((User.email == email) | (User.phone_number == phone_number)).first():
        return jsonify({"message": "Email or phone number already exists."}), 400

    # User creation
    user = User(
        username=username,
        email=email,
        password=password,  # Hash the password in production
        date_of_birth=date_of_birth,
        phone_number=phone_number,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully."}), 201


# User Login
@api_routes.route("/login", methods=["POST"])
def login_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    # Generate JWT token
    access_token = create_access_token(identity=user.id)

    return jsonify({"message": "Login successful", "access_token": access_token}), 200


# Fetch User Information
@api_routes.route("/user", methods=["GET"])
@jwt_required()
def get_user_info():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "date_of_birth": user.date_of_birth,
    })


@api_routes.route("/cart", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.json
    medicine_id = data.get("medicine_id")
    quantity = data.get("quantity", 1)

    # Check if the medicine exists and has sufficient stock
    medicine = Medicine.query.get(medicine_id)
    if not medicine or medicine.stock < quantity:
        return jsonify({"message": "Insufficient stock"}), 400

    # Get or create an active cart for the user
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

    # Check if the item already exists in the cart
    order_item = OrderItem.query.filter_by(cart_id=cart.id, medicine_id=medicine_id).first()
    if order_item:
        # Update the quantity if the item already exists
        order_item.quantity += quantity
    else:
        # Create a new order item
        order_item = OrderItem(
            cart_id=cart.id,
            medicine_id=medicine_id,
            quantity=quantity,
            price=medicine.price
        )
        db.session.add(order_item)

    # Commit the changes
    db.session.commit()

    return jsonify({"message": "Item added to cart"}), 200


# View Cart
@api_routes.route("/cart", methods=["GET"])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    cart_items = fetch_cart(user_id)
    if not cart_items:
        return jsonify({"message": "Your cart is empty"}), 200

    return jsonify(cart_items), 200


# Checkout - Initiate Payment
@api_routes.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    total_amount, message = initiate_checkout(user_id)
    if total_amount is None:
        return jsonify({"message": message}), 400

    return jsonify({
        "message": f"Checkout successful, {message}",
        "total_amount": total_amount
    }), 200


# Payment
@api_routes.route("/payment", methods=["POST"])
@jwt_required()
def payment():
    user_id = get_jwt_identity()
    data = request.json
    payment_method = data.get("payment_method", "credit_card")
    total_amount = data.get("total_amount")

    success, order_id, message = process_payment(user_id, payment_method, total_amount)
    if not success:
        return jsonify({"message": message}), 400

    return jsonify({
        "message": "Payment successful, order placed",
        "order_id": order_id
    }), 200


# Order History
@api_routes.route("/order/history", methods=["GET"])
@jwt_required()
def order_history():
    user_id = get_jwt_identity()
    try:
        order_history = view_order_history(user_id)
        return jsonify(order_history), 200
    except Exception as e:
        return jsonify({"message": "Failed to fetch order history", "error": str(e)}), 500


# Chat
@api_routes.route("/chat", methods=["POST"])
@jwt_required()
def chat_with_bot():
    user_id = get_jwt_identity()
    message = request.json.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"msg": "Message must be a non-empty string"}), 422

    conversation_flow = ConversationFlow()
    return conversation_flow.handle_message(user_id, message)


# Cancel Order
@api_routes.route("/order/cancel", methods=["POST"])
@jwt_required()
def cancel_order_route():
    user_id = get_jwt_identity()
    data = request.json
    order_id = data.get("order_id")
    if not order_id:
        return jsonify({"message": "Order ID is required"}), 400

    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"message": "Order not found for this user"}), 404

    success, message = cancel_order(order_id)
    return jsonify({"message": message}), 200 if success else 400