from datetime import datetime
from database import db
from sqlalchemy import Enum

class Medicine(db.Model):
    __tablename__ = 'medicines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    pack_size_label = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    uses = db.Column(db.String(1000), nullable=False)
    side_effects = db.Column(db.String(1000), nullable=False)
    composition = db.Column(db.String(1000), nullable=False)
    manufacturer = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Medicine {self.name}>"


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(Enum('active', 'inactive', name='cart_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('user_carts', lazy='joined'))
    order_items = db.relationship('OrderItem', backref='associated_cart', lazy=True)

    def __repr__(self):
        return f"<Cart {self.user_id} - Status {self.status}>"

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(Enum('pending', 'completed', 'cancelled', name='order_status'), default='pending')

    user = db.relationship('User', backref=db.backref('user_orders', lazy='joined'))
    order_items = db.relationship('OrderItem', backref='parent_order', lazy=True)

    def __repr__(self):
        return f"<Order {self.id} - Status {self.status}>"

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    medicine = db.relationship('Medicine', backref='medicine_order_items')

    def __repr__(self):
        return f"<OrderItem {self.medicine.name} - Quantity {self.quantity}>"

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    method = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(Enum('pending', 'completed', 'failed', name='payment_status'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime)

    user = db.relationship('User', backref='user_payments')

    def __repr__(self):
        return f"<Payment {self.id} - Status {self.status}>"
