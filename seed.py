from app import db
from models import User, Property, Lease
from werkzeug.security import generate_password_hash
from datetime import date

def seed_admin():
    # Check if the admin already exists
    admin = User.query.filter_by(username="admin1").first()

    if not admin:
        # Create the admin user
        admin = User(
            username="admin1",
            password="adminpass",  # Default password, it will be hashed
            phone="1234567890",
            unit_no="A1",
            last_name="Admin",
            role="admin"  # Admin role
        )
        
        # Hash the password
        admin.password = generate_password_hash(admin.password)
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")

def seed_users_and_properties():
    # Check if users and properties exist
    user1 = User.query.filter_by(username="resident2").first()    #change for user
    property1 = Property.query.filter_by(address="delhi").first()   #change for property seed

    # Create Property if not already in DB
    if not property1:
        property1 = Property(
            address="delhi",  # Property address
            total_units=10  # Example number of units in this property
        )
        db.session.add(property1)
        db.session.commit()
        print("Property created successfully!")
    else:
        print("Property already exists.")

    if not user1:
        # Create a User (Resident)
        user1 = User(
            username="resident2",
            password="resident123",  #default password (it will be hashed)
            phone="9876554232",  
            unit_no="102",  
            last_name="kapoor", 
            role="resident"  # Role 'resident'
        )
        
        # Hash the password
        user1.password = generate_password_hash(user1.password)
        
        # Add the user to the session
        db.session.add(user1)
        db.session.commit()
        print("User resident2 created successfully!")

    # Create Lease for the User
    lease1 = Lease.query.filter_by(user_id=user1.id, property_id=property1.id).first()

    if not lease1:
        lease1 = Lease(
            user_id=user1.id,
            property_id=property1.id,
            unit_no="102",  # Same unit as user
            lease_start=date(2024, 11, 1),  # lease start date
            lease_end=date(2024, 12, 5),  #  lease end date
            rent_rate=1500.0,  # Rent rate for the unit
            document_path="/path/to/lease/document"  # Path to lease document
        )
        db.session.add(lease1)
        db.session.commit()
        print(f"Lease for {user1.username} created successfully!")
    else:
        print("Lease already exists.")

def seed_all(app):
    with app.app_context():
        # Seed the admin user
        seed_admin()
        # Seed users and properties
        seed_users_and_properties()

if __name__ == "__main__":
    seed_all()
