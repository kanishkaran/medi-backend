from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from backend.database import db
from backend.models import User, Medicine, Cart, Order
from backend.chatbot.order_management import view_order_history
from backend.chatbot.conversation_flow import ConversationFlow
from backend.chatbot.order_management import process_payment, fetch_cart, initiate_checkout, cancel_order
from datetime import datetime
# Blueprint for API routes
api_routes = Blueprint("api_routes", __name__)

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

    access_token = create_access_token(identity=user.id)
    return jsonify({"access_token": access_token}), 200

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

# Add to Cart
@api_routes.route("/cart", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.json
    medicine_id = data.get("medicine_id")
    quantity = data.get("quantity", 1)

    # Check stock availability
    medicine = Medicine.query.get(medicine_id)
    if not medicine or medicine.stock < quantity:
        return jsonify({"message": "Insufficient stock"}), 400

    # Add to cart
    cart_item = Cart(user_id=user_id, medicine_id=medicine_id, quantity=quantity)
    db.session.add(cart_item)
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

    return jsonify([{
        "medicine_id": item.medicine.id,
        "medicine_name": item.medicine.name,
        "quantity": item.quantity,
        "price": item.medicine.price,
        "image_url": item.medicine.image_url,
    } for item in cart_items])

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
    """
    Handles user messages for the chatbot by invoking the conversation flow.
    """
    user_id = get_jwt_identity()  # Get the authenticated user ID

    # Ensure JSON is correctly parsed
    data = request.get_json(silent=True)
    print("Received request data:", data)  # Debugging log

    if not data or "message" not in data:
        return jsonify({"msg": "Invalid request: 'message' key missing"}), 422

    message = data.get("message")

    if not isinstance(message, str) or not message.strip():
        return jsonify({"msg": "Message must be a non-empty string"}), 422

    # Initialize the conversation flow instance
    conversation_flow = ConversationFlow()

    # Process the message and get the chatbot's response
    return conversation_flow.handle_message(user_id, message)

# Cancel Order
@api_routes.route("/order/cancel", methods=["POST"])
@jwt_required()
def cancel_order_route():
    data = request.json
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"message": "Order ID is required"}), 400

    user_id = get_jwt_identity()
    
    # Fetch the order to verify that it belongs to the authenticated user
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return jsonify({"message": "Order not found for this user"}), 404

    # Call the cancel_order function from the order management service
    success, message = cancel_order(order_id)
    
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"message": message}), 400
