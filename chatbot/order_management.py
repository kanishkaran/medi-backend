from datetime import datetime
from backend.database import db
from backend.models import Cart, Order, OrderItem, Medicine, Payment

def add_to_cart_service(user_id, medicine_id, quantity):
    """
    Adds a specified medicine to the user's cart.
    :param user_id: The ID of the user
    :param medicine_id: The ID of the medicine to be added
    :param quantity: The quantity of the medicine to add
    :return: A success flag and a message
    """
    # Check if the medicine exists in the database
    medicine = Medicine.query.filter_by(id=medicine_id).first()
    if not medicine:
        return False, "Medicine not found."

    # Check if the user already has a cart
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        # Create a new cart if not existing
        cart = Cart(user_id=user_id, status='active', created_at=datetime())
        db.session.add(cart)
        db.session.commit()

    # Check if the medicine is already in the cart
    cart_item = OrderItem.query.filter_by(cart_id=cart.id, medicine_id=medicine.id).first()
    if cart_item:
        # Update quantity if already in cart
        cart_item.quantity += quantity
    else:
        # Add new item to the cart
        cart_item = OrderItem(cart_id=cart.id, medicine_id=medicine.id, quantity=quantity, price=medicine.price)
        db.session.add(cart_item)

    db.session.commit()
    return True, "Medicine successfully added to your cart."

def fetch_cart(user_id):
    """
    Fetches the user's cart details.
    :param user_id: The ID of the user
    :return: A list of cart items and their details
    """
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        return []

    cart_items = OrderItem.query.filter_by(cart_id=cart.id).all()
    items = []
    for item in cart_items:
        medicine = Medicine.query.filter_by(id=item.medicine_id).first()
        items.append({
            "medicine_name": medicine.name,
            "quantity": item.quantity,
            "price": item.price,
            "total_price": item.quantity * item.price,
        })
    
    return items

def initiate_checkout(user_id):
    """
    Initiates the checkout process, calculating the total amount and redirecting to payment.
    :param user_id: The ID of the user
    :return: Total amount to be paid
    """
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        return None, "No active cart found."

    cart_items = OrderItem.query.filter_by(cart_id=cart.id).all()
    if not cart_items:
        return None, "Cart is empty."

    # Calculate total amount for checkout
    total_amount = 0
    for item in cart_items:
        total_amount += item.quantity * item.price

    # Proceed to the payment page
    return total_amount, "Proceed to payment."

def process_payment(user_id, payment_method, total_amount):
    """
    Processes the payment for the order. In a real implementation, this will interface
    with a payment gateway to complete the transaction.
    :param user_id: The ID of the user
    :param payment_method: The method of payment (e.g., Credit Card, PayPal)
    :param total_amount: The total amount to be paid
    :return: A success flag, order ID, and a message
    """
    # Placeholder for real payment gateway integration
    # Example: You would make an API call to your payment processor here (e.g., Stripe, Razorpay, etc.)
    # If the payment is successful, proceed with creating the order.
    
    # For now, let's simulate a successful payment and proceed with order completion
    # In a real-world scenario, handle the payment gateway response here.

    payment = Payment(user_id=user_id, method=payment_method, amount=total_amount, status='pending', created_at=datetime())
    db.session.add(payment)
    db.session.commit()

    # Assuming payment is successful, change status to 'completed'
    payment.status = 'completed'
    db.session.commit()

    # Now that the payment is complete, create the order
    return complete_order(user_id, total_amount)

def complete_order(user_id, total_amount):
    """
    Completes the order after successful payment and moves items to the order.
    :param user_id: The ID of the user
    :param total_amount: The total amount paid
    :return: A success flag, order ID, and a message
    """
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        return False, None, "No active cart found."

    cart_items = OrderItem.query.filter_by(cart_id=cart.id).all()
    if not cart_items:
        return False, None, "Cart is empty."

    # Create a new order
    order = Order(user_id=user_id, created_at=datetime(), status='completed', total_amount=total_amount)
    db.session.add(order)
    db.session.commit()

    # Move items from cart to order
    for item in cart_items:
        order_item = OrderItem(order_id=order.id, medicine_id=item.medicine_id, quantity=item.quantity, price=item.price)
        db.session.add(order_item)
        db.session.delete(item)

    cart.status = 'completed'  # Mark the cart as completed
    db.session.commit()

    return True, order.id, f"Order #{order.id} placed successfully with total amount: ${total_amount}"

def cancel_order(order_id):
    """
    Cancels an order and restores the stock of medicines.
    :param order_id: The ID of the order to be canceled
    :return: A success flag and a message
    """
    order = Order.query.filter_by(id=order_id).first()
    if not order:
        return False, "Order not found."

    if order.status == 'canceled':
        return False, "Order has already been canceled."

    # Update the order status to canceled
    order.status = 'canceled'
    db.session.commit()

    # Restore stock of medicines in the canceled order
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    for item in order_items:
        medicine = Medicine.query.filter_by(id=item.medicine_id).first()
        medicine.stock += item.quantity
        db.session.commit()

    return True, "Order has been canceled and stock restored."

def view_order_history(user_id):
    """
    Retrieves the order history for a user.
    :param user_id: The ID of the user
    :return: A list of orders and their details
    """
    orders = Order.query.filter_by(user_id=user_id).all()
    order_history = []
    for order in orders:
        items = []
        total_amount = 0
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        for item in order_items:
            medicine = Medicine.query.filter_by(id=item.medicine_id).first()
            items.append({
                "medicine_name": medicine.name,
                "quantity": item.quantity,
                "price": item.price,
                "total_price": item.quantity * item.price,
            })
            total_amount += item.quantity * item.price

        order_history.append({
            "order_id": order.id,
            "created_at": order.created_at,
            "total_amount": total_amount,
            "status": order.status,
            "items": items
        })

    return order_history
