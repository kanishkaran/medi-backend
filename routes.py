from flask import Blueprint, jsonify, request
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .database import db
from .models import User, Medicine, Cart, Order, OrderItem
from .chatbot.order_management import view_order_history, complete_order, fetch_cart, initiate_checkout, cancel_order
from .chatbot.conversation_flow import ConversationFlow
from datetime import datetime, date
import stripe
import requests as http_requests
import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import pickle

# Initialize Stripe client
stripe.api_key = "sk_test_51R8nH7CY9tdh1bLP5EWofkR41f7gG6bFdCVFyMo9Oexy2zxhhWcL4ps7MdqsrvURnVuYQ1td7zK4NspvCzr9eFMI00HTObWS8W"

# Blueprint for API routes
api_routes = Blueprint("api_routes", __name__)


# Load the handwriting recognition model
MODEL_PATH = "models/my_model-85ac.h5"  # Replace with the actual path to your model
model = load_model(MODEL_PATH)

# Load the label encoder
LABEL_ENCODER_PATH = "models/label_encoder.pkl"  # Replace with the actual path to your label encoder
with open(LABEL_ENCODER_PATH, "rb") as file:
    label_encoder = pickle.load(file)

# Define the image preprocessing function
def preprocess_image(image):
    """
    Preprocess the input image to match the model's requirements.
    """
    image = image.convert("L")  # Convert to grayscale
    image = image.resize((128, 32))  # Resize to match model input
    image = img_to_array(image) / 255.0  # Normalize pixel values
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image

# Handwriting Recognition Endpoint
@api_routes.route("/recognize", methods=["POST"])
def recognize_handwriting():
    """
    Endpoint to recognize handwriting from an uploaded image.
    """
    if "image" not in request.files:
        return jsonify({"message": "No image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    try:
        # Load and preprocess the image
        image = Image.open(file.stream)
        processed_image = preprocess_image(image)

        # Predict the label using the model
        prediction = model.predict(processed_image)
        predicted_label_index = np.argmax(prediction, axis=-1)[0]

        # Decode the predicted label using the label encoder
        predicted_label = label_encoder.inverse_transform([predicted_label_index])[0]

        return jsonify({"predicted_label": predicted_label}), 200
    except Exception as e:
        return jsonify({"message": "Failed to process the image", "error": str(e)}), 500


# Google Login Route
@api_routes.route("/login/google", methods=["POST"])
def google_login():
    data = request.json
    token = data.get("token")  # This is the OAuth 2.0 access token

    if not token:
        return jsonify({"message": "Token is required"}), 400

    try:
        # Use the access token to fetch user info from Google's UserInfo endpoint
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {token}"}

        userinfo_response = http_requests.get(userinfo_url, headers=headers)
        if userinfo_response.status_code != 200:
            return jsonify({"message": "Failed to fetch user info", "error": userinfo_response.json()}), 401

        userinfo = userinfo_response.json()

        # Extract user information
        email = userinfo.get("email")
        username = userinfo.get("name", email.split("@")[0])
        picture = userinfo.get("picture")
        date_of_birth = None
        phone_number = None

        # Use the access token to fetch additional information from Google People API
        people_api_url = "https://people.googleapis.com/v1/people/me?personFields=birthdays,phoneNumbers"
        people_response = http_requests.get(people_api_url, headers=headers)
        if people_response.status_code == 200:
            people_data = people_response.json()

            # Extract date of birth
            if "birthdays" in people_data:
                dob_data = people_data["birthdays"][0].get("date", {})
                if dob_data:
                    # Convert the date to a Python date object
                    year = dob_data.get("year", 0)
                    month = dob_data.get("month", 0)
                    day = dob_data.get("day", 0)
                    if year and month and day:
                        date_of_birth = date(year, month, day)

            # Extract phone number
            if "phoneNumbers" in people_data:
                phone_number = people_data["phoneNumbers"][0].get("value")
                
        if not phone_number:
            phone_number = "N/A"  # Use a default value or placeholder

        # Check if the user already exists
        user = User.query.filter_by(email=email).first()
        if not user:
            # Create a new user if not already registered
            user = User(
                username=username,
                email=email,
                password="",  # No password for Google login
                date_of_birth=date_of_birth,
                phone_number=phone_number,
                created_at=datetime.utcnow()
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
                "email": user.email,
                "date_of_birth": user.date_of_birth,
                "phone_number": user.phone_number,
                "picture": picture
            }
        }), 200

    except Exception as e:
        return jsonify({"message": "Failed to log in with Google", "error": str(e)}), 500
        
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

# Cart Operations
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

@api_routes.route("/cart", methods=["GET"])
@jwt_required()
def view_cart():
    user_id = get_jwt_identity()
    cart_items = fetch_cart(user_id)
    if not cart_items:
        return jsonify({"message": "Your cart is empty"}), 200

    return jsonify(cart_items), 200

@api_routes.route("/cart/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_cart_item(item_id):
    user_id = get_jwt_identity()
    try:
        # Find the cart item by ID and ensure it belongs to the user
        cart_item = OrderItem.query.join(Cart).filter(
            OrderItem.medicine_id == item_id, Cart.user_id == user_id, Cart.status == 'active'
        ).first()

        if not cart_item:
            return jsonify({"message": "Item not found or does not belong to the user"}), 404

        # Delete the item from the database
        db.session.delete(cart_item)
        db.session.commit()

        return jsonify({"message": "Item deleted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to delete item", "error": str(e)}), 500

# Checkout
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


# Payment: Create Stripe Payment Intent
@api_routes.route("/payment/intent", methods=["POST"])
@jwt_required()
def create_payment_intent():
    user_id = get_jwt_identity()
    data = request.json
    amount = data.get("amount")  # Amount in INR (e.g., 500 for ₹500)

    if not amount or amount <= 0:
        return jsonify({"message": "Invalid amount"}), 400

    try:
        # Create Stripe Payment Intent with multiple payment methods
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Amount in paise
            currency="inr",
            payment_method_types=["card"],  # Add other methods
        )

        return jsonify({
            "client_secret": intent["client_secret"],
            "payment_intent_id": intent["id"],  # Include payment_intent_id
            "amount": amount,
            "currency": "INR"
        }), 200
    except Exception as e:
        return jsonify({"message": "Failed to create payment intent", "error": str(e)}), 500

@api_routes.route("/payment/verify", methods=["POST"])
@jwt_required()
def verify_payment():
    user_id = get_jwt_identity()
    data = request.json
    payment_intent_id = data.get("payment_intent_id")

    if not payment_intent_id:
        return jsonify({"message": "Payment Intent ID is required"}), 400

    try:
        # Log the payment_intent_id for debugging
        print(f"Received payment_intent_id: {payment_intent_id}")

        # Step 1: Retrieve the Payment Intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        print(f"Retrieved Payment Intent: {intent}")

        # Step 2: Validate the Payment Status
        if intent["status"] == "succeeded":
            # Payment is successful, complete the order
            total_amount = intent["amount"] / 100  # Convert from paise to INR
            print(f"Payment succeeded. Total amount: {total_amount}")

            # Call the complete_order function
            success, order_id, message = complete_order(user_id, total_amount)
            print(f"Order completion status: {success}, Order ID: {order_id}, Message: {message}")

            if success:
                return jsonify({
                    "message": f"Payment verified and order #{order_id} completed successfully.",
                    "order_id": order_id
                }), 200
            else:
                return jsonify({"message": message}), 400
        else:
            print(f"Payment not successful. Status: {intent['status']}")
            return jsonify({"message": f"Payment not successful. Status: {intent['status']}"}), 400

    except Exception as e:
        # Log the error for debugging
        print(f"Error in /payment/verify: {str(e)}")
        return jsonify({"message": "Failed to verify payment", "error": str(e)}), 500


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