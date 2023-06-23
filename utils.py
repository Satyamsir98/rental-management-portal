from flask_mail import Message
from extensions import mail

def send_email(subject, recipient, body):
    """Sends an email notification."""
    msg = Message(subject=subject, recipients=[recipient])
    msg.body = body
    mail.send(msg)
