import pytz
from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# User Table
class User(UserMixin, db.Model):  # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    unit_no = db.Column(db.String(10), nullable=True)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'resident' or 'admin'

    def __repr__(self):
        return f"<User {self.username}>"

    # Flask-Login required methods
    def get_id(self):
        return str(self.id) 
    
    def is_active(self):
        return True  # can modify this logic if you need to deactivate users
    
    def is_authenticated(self):
        return True  # can modify this logic to check if the user is authenticated
    
    def is_anonymous(self):
        return False  # we are not using anonymous users, this is always False
     # Hash the password before storing it
    def set_password(self, password):
        self.password = generate_password_hash(password)  # Hash the password

    # Check if the entered password matches the hashed password
    def check_password(self, password):
        return check_password_hash(self.password, password)  # Verify hashed password

# Property Table
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(200), nullable=False)
    total_units = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Property {self.address}>"

# Lease Table
class Lease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    unit_no = db.Column(db.String(10), nullable=False)
    lease_start = db.Column(db.Date, nullable=False)
    lease_end = db.Column(db.Date, nullable=False)
    rent_rate = db.Column(db.Float, nullable=False)
    document_path = db.Column(db.String(200), nullable=False)

    user = db.relationship('User', backref=db.backref('leases', lazy=True))
    property = db.relationship('Property', backref=db.backref('leases', lazy=True))

    def __repr__(self):
        return f"<Lease {self.unit_no}>"

# MaintenanceRequest Table
class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue_description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Plumbing, electrical, etc.
    severity = db.Column(db.String(20), nullable=False)  # Low, medium, high
    status = db.Column(db.String(20), default='Open')  # Open, in progress, closed, etc.
    comments = db.Column(db.Text, nullable=True)

    user = db.relationship('User', backref=db.backref('maintenance_requests', lazy=True))

    def __repr__(self):
        return f"<MaintenanceRequest {self.id}>"

# Payment Table
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    date_paid = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)  # Bank, Credit Card, etc.
    processing_fee = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)  # this Includes processing fee

    user = db.relationship('User', backref=db.backref('payments', lazy=True))

    def calculate_processing_fee(self):
        """
        Calculate the processing fee based on the payment method.
        """
        if self.payment_method.lower() in ['credit card', 'debit card']:
            self.processing_fee = self.amount_paid * 0.028  # 2.8% processing fee
        else:
            self.processing_fee = 0.0  # No fee for bank accounts
        self.total_amount = self.amount_paid + self.processing_fee

    def __repr__(self):
        return f"<Payment ID: {self.id}, User ID: {self.user_id}, Amount: {self.amount_paid}, Total: {self.total_amount}>"


# Notification Table
IST = pytz.timezone('Asia/Kolkata')
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Unread')  # Read, Unread

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f"<Notification {self.id}>"
