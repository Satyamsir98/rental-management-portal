import pytest
from app import app
from extensions import db
from models import User, Property, Lease, MaintenanceRequest, Payment, Notification

@pytest.fixture
def test_client():
    """Setting up the Flask test client with an in-memory database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking for SQLAlchemy
    app.config['SECRET_KEY'] = 'test_secret_key'  # Secret key for testing

    # Creating a test client and set up the database
    with app.test_client() as testing_client:
        with app.app_context():
            db.create_all()  # Creating the necessary tables for in-memory database

            # Insert initial test data
            admin_user = User(
                username="admin", password="password", phone="1234561890", 
                unit_no=None, last_name="Admin", role="admin"
            )
            admin_user.set_password("password")
            db.session.add(admin_user)

            resident_user = User(
                username="resident", password="password", phone="0987100432", 
                unit_no="101", last_name="Resident", role="resident"
            )
            resident_user.set_password("password")
            db.session.add(resident_user)

            db.session.commit()  # Committig the test users to the database

            yield testing_client  # Providing the test client for testing

            db.session.remove()  # Clean up the session
            db.drop_all()  # Drop all tables to after tests
