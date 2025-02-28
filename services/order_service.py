from backend.database import db
from backend.models import Cart, OrderItem, Medicine

def checkout_order(user_id):
    """
    Process the user's cart and create an order.
    :param user_id: ID of the user
    :return: Tuple (success, order_id, message)
    """
    # Fetch user's cart
    query_cart = """
        SELECT medicine_id, quantity 
        FROM carts 
        WHERE user_id = %s
    """
    cart_items = db.fetch_all(query_cart, (user_id,))
    if not cart_items:
        return False, None, "Cart is empty."

    # Create order
    insert_order_query = """
        INSERT INTO orders (user_id, total_price)
        VALUES (%s, %s) RETURNING id
    """
    total_price = sum(item['quantity'] * fetch_price(item['medicine_id']) for item in cart_items)
    order_id = db.execute_returning(insert_order_query, (user_id, total_price))
    
    # Add cart items to order details
    insert_order_details_query = """
        INSERT INTO order_details (order_id, medicine_id, quantity)
        VALUES (%s, %s, %s)
    """
    for item in cart_items:
        db.execute(insert_order_details_query, (order_id, item['medicine_id'], item['quantity']))
    
    # Clear user's cart
    delete_cart_query = "DELETE FROM carts WHERE user_id = %s"
    db.execute(delete_cart_query, (user_id,))

    return True, order_id, "Checkout successful."


def fetch_cart(user_id):
    """
    Retrieve the current cart for a user.
    :param user_id: ID of the user
    :return: List of cart items with medicine details and quantities
    """
    try:
        # Query the Cart and OrderItem tables using SQLAlchemy ORM
        query = (
            db.session.query(
                OrderItem.medicine_id,
                Medicine.name,
                OrderItem.quantity
            )
            .join(Medicine, OrderItem.medicine_id == Medicine.id)
            .join(Cart, OrderItem.cart_id == Cart.id)
            .filter(Cart.user_id == user_id, Cart.status == 'active')
        )

        # Fetch all results
        results = query.all()

        # Format the results into a list of dictionaries
        cart_items = [
            {"medicine_id": result[0], "name": result[1], "quantity": result[2]}
            for result in results
        ]

        return cart_items

    except Exception as e:
        return f"Error: {str(e)}"
    
    
def add_to_cart_service(user_id, medicine_id, quantity):
    """
    Adds a medicine to the user's cart or updates the quantity if already present.
    :param user_id: ID of the user
    :param medicine_id: ID of the medicine
    :param quantity: Quantity to add
    :return: Tuple (success, message)
    """
    # Check if medicine already in cart
    query_check = """
        SELECT quantity 
        FROM carts 
        WHERE user_id = %s AND medicine_id = %s
    """
    existing_item = db.fetch_one(query_check, (user_id, medicine_id))

    if existing_item:
        # Update quantity
        update_query = """
            UPDATE carts 
            SET quantity = quantity + %s 
            WHERE user_id = %s AND medicine_id = %s
        """
        db.execute(update_query, (quantity, user_id, medicine_id))
    else:
        # Add new item
        insert_query = """
            INSERT INTO carts (user_id, medicine_id, quantity)
            VALUES (%s, %s, %s)
        """
        db.execute(insert_query, (user_id, medicine_id, quantity))

    return True, "Item added to cart successfully."

def fetch_price(medicine_id):
    """
    Fetches the price of a medicine by its ID.
    :param medicine_id: ID of the medicine
    :return: Price of the medicine
    """
    query = "SELECT price FROM medicines WHERE id = %s"
    result = db.fetch_one(query, (medicine_id,))
    return result['price'] if result else 0
