from datetime import datetime, timedelta
from flask import current_app as app
import pytz
from extensions import db
from models import Lease, Notification,User 
from utils import send_email

def check_due_dates():
    with app.app_context():
        """Notify residents of upcoming payment due dates."""
        print('inside due dates')
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

        # Convert the time to IST (Indian Standard Time)
        india_tz = pytz.timezone('Asia/Kolkata')
        now= now_utc.astimezone(india_tz)
        notification_threshold = now + timedelta(days=5) # Calculate 5 days ahead
        # Query leases where lease_end is within 5 days from now
        leases = Lease.query.filter(Lease.lease_end <= notification_threshold, Lease.lease_end > now).all()

        for lease in leases:
            user = lease.user
            due_amount = lease.rent_rate  #rent_rate is the due amount

            # in-app notification
            message = f"Reminder: Your payment of {due_amount} is due on {lease.lease_end.strftime('%Y-%m-%d')}."
            notification = Notification(user_id=user.id, message=message)
            db.session.add(notification)

            # # Send email notification
            # with app.app_context():
            #     send_email(
            #         subject="Payment Due Reminder",
            #         recipient=user.username,
            #         body=message
            #     )

        db.session.commit()
