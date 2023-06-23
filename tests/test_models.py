from models import User, Property, Lease, MaintenanceRequest, Payment, Notification
from extensions import db
from datetime import datetime, timedelta

def test_user_creation(test_client):
    user = User(username="testuser", phone="1432576890", last_name="khanna", role="resident")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    retrieved_user = User.query.filter_by(username="testuser").first()
    assert retrieved_user is not None
    assert retrieved_user.check_password("password123") is True
    assert retrieved_user.phone == "1432576890"

def test_property_creation(test_client):
    property_ = Property(address="123 Test St", total_units=10)
    db.session.add(property_)
    db.session.commit()

    retrieved_property = Property.query.filter_by(address="123 Test St").first()
    assert retrieved_property is not None
    assert retrieved_property.total_units == 10

def test_lease_creation(test_client):
    user = User(username="leaseuser", phone="9856743210", last_name="Sharma", role="resident")
    user.set_password("password123")
    property_ = Property(address="456 Lease St", total_units=5)
    db.session.add(user)
    db.session.add(property_)
    db.session.commit()

    lease = Lease(
        user_id=user.id, property_id=property_.id, unit_no="101",
        lease_start=datetime.now(), lease_end=datetime.now() + timedelta(days=365),
        rent_rate=1200.00, document_path="/leases/doc.pdf"
    )
    db.session.add(lease)
    db.session.commit()

    retrieved_lease = Lease.query.filter_by(unit_no="101").first()
    assert retrieved_lease is not None
    assert retrieved_lease.rent_rate == 1200.00

def test_payment_calculation(test_client):
    user = User(username="payuser", phone="1122774455", last_name="Brown", role="resident")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    payment = Payment(user_id=user.id, amount_paid=1000.00, payment_method="credit card")
    payment.calculate_processing_fee()
    db.session.add(payment)
    db.session.commit()

    assert payment.processing_fee == 28.00  # 2.8% of 1000
    assert payment.total_amount == 1028.00

def test_notification_creation(test_client):
    user = User(username="notifyuser", phone="9988776565", last_name="Test", role="resident")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    notification = Notification(user_id=user.id, message="Test notification")
    db.session.add(notification)
    db.session.commit()

    retrieved_notification = Notification.query.filter_by(user_id=user.id).first()
    assert retrieved_notification is not None
    assert retrieved_notification.status == "Unread"
