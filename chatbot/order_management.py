from datetime import datetime
from database import db
from models import Cart, Order, OrderItem, Medicine

def fetch_cart(user_id):
    """
    Fetches the user's cart details.
    :param user_id: The ID of the user
    :return: A list of cart items and their details
    """
    # Fetch the active cart for the user
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        return []

    # Use the relationship between Cart and OrderItem to fetch cart items
    items = []
    for item in cart.order_items:  # Assuming `order_items` is a relationship in the Cart model
        items.append({
            "medicine_id": item.medicine.id,  # Access the related Medicine object
            "medicine_name": item.medicine.name,
            "quantity": item.quantity,
            "price": item.price,
            "total_price": item.quantity * item.price,
            "image_url": item.medicine.image_url,  # Assuming Medicine has an image_url field
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

def complete_order(user_id, total_amount):
    cart = Cart.query.filter_by(user_id=user_id, status='active').first()
    if not cart:
        return False, None, "No active cart found."

    cart_items = OrderItem.query.filter_by(cart_id=cart.id).all()
    if not cart_items:
        return False, None, "Cart is empty."

    order = Order(user_id=user_id, created_at=datetime.now(), status='completed', total_amount=total_amount)
    db.session.add(order)
    db.session.commit()

    for item in cart_items:
        order_item = OrderItem(order_id=order.id, medicine_id=item.medicine_id, quantity=item.quantity, price=item.price)
        db.session.add(order_item)
        db.session.delete(item)

    cart.status = 'inactive'
    db.session.commit()

    return True, order.id, f"Order #{order.id} placed successfully with total amount: ₹{total_amount}"

def cancel_order(order_id):
    """
    Cancels an order and restores the stock of medicines.
    :param order_id: The ID of the order to be canceled
    :return: A success flag and a message
    """
    order = Order.query.filter_by(id=order_id).first()
    if not order:
        return False, "Order not found."

    if order.status == 'cancelled':
        return False, "Order has already been canceled."

    # Update the order status to canceled
    order.status = 'cancelled'
    db.session.commit()

    # Restore stock of medicines in the canceled order
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    for item in order_items:
        medicine = Medicine.query.filter_by(id=item.medicine_id).first()
        medicine.stock += item.quantity
    db.session.commit()

    return True, "Order has been canceled and stock restored."

def view_order_history(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    order_history = []
    for order in orders:
        items = []
        for item in order.order_items:
            items.append({
                "id": item.id,
                "name": item.medicine.name,
                "quantity": item.quantity,
                "price": item.price,
                "total_price": item.quantity * item.price,
            })

        order_history.append({
            "id": order.id,
            "createdAt": order.created_at.isoformat(),
            "total": order.total_amount,
            "status": order.status,
            "items": items
        })

    return order_history