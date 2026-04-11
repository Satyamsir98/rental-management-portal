from datetime import datetime
from functools import wraps
from flask import Flask, abort, g, render_template, redirect, session, url_for, flash, request
from flask_mail import Mail, Message
from extensions import mail 
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required
from extensions import db
from models import User, Payment, Property, MaintenanceRequest, Lease, Notification
from forms import SignUpForm
from werkzeug.security import generate_password_hash,check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler import check_due_dates
from apscheduler.triggers.interval import IntervalTrigger
import logging
from seed import seed_all


# Initializing Flask app
app = Flask(__name__)
app.config.from_object('config') 

# Configuring app settings
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
logging.basicConfig(level=logging.DEBUG)


# Initializing database and migration tool
db.init_app(app)
migrate = Migrate(app, db)



# Initializing the scheduler
scheduler = BackgroundScheduler(daemon = True)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'  


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Route
@app.route('/')
def home():
    if 'user_id' not in session:
        # If no user is logged in, redirect to the login page
        return redirect(url_for('login'))
    
    # Retrieving user information from the session 
    user = db.session.get(User, session['user_id'])

    # Ensuring user exists
    if user is None:
        # Redirecting to login page if the user doesn't exist 
        return redirect(url_for('login'))
    
    # Redirecting to the dashboards based on the user role
    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))  # admin page redirect
    else:
        return redirect(url_for('user_dashboard'))  # user page redirect

# Role Required Decorator
def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if session.get('role') != role:
                flash("Access denied. You don't have permission to view this page.", "danger")
                return redirect(url_for('home'))
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@role_required('admin')
@login_required
def admin_dashboard():
    # Ensure only admins can access this
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')  
    else:
        flash("Access denied!", "danger")
        return redirect(url_for('login'))
    
@app.route('/user/dashboard')
@role_required('resident')
@login_required
def user_dashboard():
    # Ensure user is a resident (and not an admin)
    if session.get('role') != 'resident':
        flash("Access denied.", "danger")
        return redirect(url_for('home'))

    return render_template('user_dashboard.html')


@app.route('/lease')
@role_required('resident')
@login_required
def lease():
    user_id = session.get('user_id')
    lease = Lease.query.filter_by(user_id=user_id).first()
    if lease:
        return render_template('lease.html', lease=lease)
    else:
        flash("No lease information found.", "warning")
        return redirect(url_for('home'))

@app.route('/maintenance', methods=['GET', 'POST'])
@role_required('resident')
@login_required
def maintenance():
    user_id = session.get('user_id')  # Get the current user's ID
    if request.method == 'POST':
        issue_description = request.form['issue_description']
        category = request.form['category']
        severity = request.form['severity']

        # Create a new maintenance request and add it to the database
        maintenance_request = MaintenanceRequest(
            user_id=user_id,
            issue_description=issue_description,
            category=category,
            severity=severity,
            status='Open'  # Default status 
        )

        db.session.add(maintenance_request)
        db.session.commit()

        flash('Your maintenance request has been submitted!', 'success')
        return redirect(url_for('home'))

    return render_template('maintenance.html')


@app.route('/view_maintenance')
@role_required('resident')
@login_required
def view_maintenance():
    user_id = session.get('user_id')
    maintenance_requests = MaintenanceRequest.query.filter_by(user_id=user_id).all()

    return render_template('view_maintenance.html', maintenance_requests=maintenance_requests)

@app.route('/payments')
@role_required('resident')
def payments():
    if not session.get('user_id'):
        flash("You need to log in to view your payment history.", "warning")
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user_payments = Payment.query.filter_by(user_id=user_id).all()
    return render_template('payments.html', payments=user_payments)

@app.route('/submit_payment', methods=['GET', 'POST'])
@role_required('resident')
@login_required
def submit_payment():
    if request.method == 'POST':
        user_id = session.get('user_id')
        amount_paid = float(request.form['amount_paid'])
        payment_method = request.form['payment_method']

        # Create a new payment
        payment = Payment(
            user_id=user_id,
            amount_paid=amount_paid,
            payment_method=payment_method
        )
        
        # Calculate processing fee and total amount
        payment.calculate_processing_fee()
        
        # Add to database
        db.session.add(payment)
        db.session.commit()

        flash(f"Payment of {amount_paid} submitted successfully! Total: {payment.total_amount:.2f}", "success")
        return redirect(url_for('payments'))
    
    return render_template('submit_payment.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        # Hash password and store it
        hashed_password = generate_password_hash(form.password.data)

        # Create a new user
        new_user = User(
            username=form.username.data,
            password=hashed_password,
            phone=form.phone.data,
            last_name=form.last_name.data,
            role='resident'  # Default role for registration
        )
        
        # Add to the database
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        # Flash success message and redirecting to login page
        flash('Signed up successfully! You are now logged in.', 'success')
        return redirect(url_for('home'))

    return render_template('signup.html', form=form) 


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):  # Verify the password
            # Store user details in the session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role  # Store the role in session

            # Print session data to console
            print("Session Data:", session)

            flash('Login successful!', 'success')  # Flash nesaage success

            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))  
            else:
                return redirect(url_for('home'))  
        else:
            flash('Invalid username or password', 'danger')  #error message if credentials are incorrect

    return render_template('login.html')  # Rendering the login form

#//////////////////ADMIIN SECTION ROUTES////////////////////////////
@app.route('/admin/manage_properties', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def manage_properties():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    # If the form is submitted to add a new property
    if request.method == 'POST':
        address = request.form['address']
        total_units = request.form['total_units']
        property = Property(address=address, total_units=total_units)
        db.session.add(property)
        db.session.commit()
        flash("Property added successfully!", "success")

    properties = Property.query.all()  # Get all properties to display
    return render_template('admin/manage_properties.html', properties=properties)


@app.route('/admin/properties/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_property():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        address = request.form['address']
        total_units = request.form['total_units']
        
        new_property = Property(address=address, total_units=total_units)
        db.session.add(new_property)
        db.session.commit()
        flash("Property added successfully.", "success")
        return redirect(url_for('manage_properties'))
    
    return render_template('admin/add_property.html')


@app.route('/admin/properties/edit/<int:property_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_property(property_id):
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    property = Property.query.get_or_404(property_id)
    if request.method == 'POST':
        property.address = request.form['address']
        property.total_units = request.form['total_units']
        db.session.commit()
        flash("Property updated successfully.", "success")
        return redirect(url_for('manage_properties'))
    
    return render_template('admin/edit_property.html', property=property)


@app.route('/admin/properties/delete/<int:property_id>', methods=['POST'])
@role_required('admin')
@login_required
def delete_property(property_id):
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    property = Property.query.get_or_404(property_id)
    db.session.delete(property)
    db.session.commit()
    flash("Property deleted successfully.", "success")
    return redirect(url_for('manage_properties'))

@app.route('/admin/view_all_leases')
@role_required('admin')
@login_required
def view_all_leases():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    leases = Lease.query.all()  # Get all leases from the database
    return render_template('admin/view_all_leases.html', leases=leases)

@app.route('/admin/view_maintenance_requests')
@role_required('admin')
@login_required
def view_maintenance_requests():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    # Fetch all maintenance requests
    maintenance_requests = MaintenanceRequest.query.all()

    return render_template('admin/view_maintenance_requests.html', maintenance_requests=maintenance_requests)

@app.route('/admin/edit_maintenance_request/<int:request_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_maintenance_request(request_id):
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    maintenance_request = MaintenanceRequest.query.get_or_404(request_id)

    if request.method == 'POST':
        # form submission to update status and comments
        maintenance_request.status = request.form['status']
        maintenance_request.comments = request.form['comments']
        db.session.commit()
        flash("Maintenance request updated successfully!", "success")
        return redirect(url_for('view_maintenance_requests'))

    return render_template('admin/edit_maintenance_request.html', maintenance_request=maintenance_request)

@app.route('/admin/generate_reports')
@role_required('admin')
@login_required
def generate_reports():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    # Get all users with their lease and payment information
    users = User.query.all()
    reports = []

    for user in users:
        for lease in user.leases:  # Loop over each lease of the user
            # Get the latest payment for the user (if any)
            latest_payment = Payment.query.filter_by(user_id=user.id).order_by(Payment.date_paid.desc()).first()

            if latest_payment:
                processing_fee = latest_payment.processing_fee
                total_amount_paid = latest_payment.amount_paid + processing_fee
                balance = max(0, lease.rent_rate - latest_payment.amount_paid)
                payment_status = f"{latest_payment.amount_paid + processing_fee:.2f}"
            else:
                processing_fee = 0
                total_amount_paid = 0
                balance = lease.rent_rate
                payment_status = "Not Paid Yet"

            reports.append({
                'user': user,
                'lease': lease,
                'last_payment': latest_payment,
                'balance': balance,
                'total_amount_paid': total_amount_paid,  #total amount paid addeed
                'payment_status': payment_status,        # payment status added
                'due_date': lease.lease_end
            })

    return render_template('admin/generate_reports.html', reports=reports)


@app.route('/admin/view_users', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def view_all_users():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('home'))

    users = User.query.all()  # Fetching all users
    properties = Property.query.all()  # Fetching all properties
    current_date = datetime.today().date()  # today's date

    if request.method == 'POST':
        action = request.form.get('action')  #Identify the action

        if action == 'assign_lease':
            # Assign a lease
            user_id = request.form.get('user_id')
            property_id = request.form.get('property_id')
            unit_no = request.form.get('unit_no')
            lease_start = request.form.get('lease_start')
            lease_end = request.form.get('lease_end')
            rent_rate = request.form.get('rent_rate')
            document_path = request.form.get('document_path')

            # Checking for missing data
            if not user_id or not property_id or not unit_no or not lease_start or not lease_end or not rent_rate:
                flash("All fields are required to assign a lease.", "danger")
                return redirect(url_for('view_all_users'))

            # Checking if the user already has a lease for the given unit
            existing_lease = Lease.query.filter_by(user_id=user_id, unit_no=unit_no).first()
            if existing_lease:
                # If the user has an existing lease for the unit, delete it before adding a new one
                db.session.delete(existing_lease)

            # Creating a new lease
            new_lease = Lease(
                user_id=user_id,
                property_id=property_id,
                unit_no=unit_no,
                lease_start=datetime.strptime(lease_start, "%Y-%m-%d"),
                lease_end=datetime.strptime(lease_end, "%Y-%m-%d"),
                rent_rate=float(rent_rate),
                document_path=document_path or "No Document"
            )
            db.session.add(new_lease)
            db.session.commit()

            flash("Lease assigned successfully!", "success")
            return redirect(url_for('view_all_users'))

        elif action == 'delete_user':
            # Delete a user
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)

            if not user:
                flash("User not found.", "danger")
                return redirect(url_for('view_all_users'))

            # Delete all related leases, payments, and maintenance requests
            Lease.query.filter_by(user_id=user.id).delete()  # Deleting leases
            Payment.query.filter_by(user_id=user.id).delete()  # Deletng payments
            MaintenanceRequest.query.filter_by(user_id=user.id).delete()  # Deleting maintenance requests
            
            # Delete the user
            db.session.delete(user)
            db.session.commit()

            flash("User and all related data deleted successfully!", "success")
            return redirect(url_for('view_all_users'))

    # the latest lease only for each user
    user_data = []
    for user in users:
        leases = Lease.query.filter_by(user_id=user.id).order_by(Lease.lease_start.desc()).limit(1).all()  # the most recent lease only
        user_data.append({'user': user, 'leases': leases})

    return render_template('admin/view_users.html', user_data=user_data, properties=properties, current_date=current_date)


@app.route('/dashboard_redirect')
@login_required
def dashboard_redirect():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard
    else:
        return redirect(url_for('home'))  # Redirect to the user's dashboard

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('Logged out successfully.', 'info')  #logout success message
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/notifications')
@login_required
def view_notifications():
    user_id = session.get('user_id')
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.date.desc()).all()
    return render_template('notifications.html', notifications=notifications)

@app.before_request
def load_notifications():
    if 'user_id' in session:
        g.unread_count = Notification.query.filter_by(user_id=session['user_id'], status='Unread').count()
    else:
        g.unread_count = 0


#///////////////////// Mail initialization/////////////////
# # Configure Flask-Mail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Example: Use your actual mail server
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'rentalmamangementapp@gmail.com'
# app.config['MAIL_PASSWORD'] = 'Satyam123'
# app.config['MAIL_DEFAULT_SENDER'] = 'rentalmamangementapp@gmail.com'

# # Initialize Flask-Mail
# mail.init_app(app)

# def send_email(to, subject, body):
#     msg = Message(subject, recipients=[to], body=body)
#     mail.send(msg)

#//////////////  logging ///////////////
# Create logger
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,  # Change to ERROR in production
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {error}")
    return "Internal Server Error", 500

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"Page not found: {error}")
    return "Page Not Found", 404


#/////////////////////////////////////////////////////////////////////////////
# Create all tables
with app.app_context():
    db.create_all()
    from models import User
    if not User.query.first():
        print("Seeding database...")
        seed_all(app)
    else:
        print("Database already seeded, skipping...")  
    print("Tables created successfully!")
    if not scheduler.running:
        scheduler.start()
        print("sghecduler started")
        def send_due_notifications_job():
            with app.app_context():  
                check_due_dates()
        scheduler.add_job(func=check_due_dates, trigger="interval", days=1,timezone='Asia/Kolkata')
        # scheduler.add_job(func=send_due_notifications_job, trigger=IntervalTrigger(minutes=1, timezone='Asia/Kolkata'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    # app.run(debug=True)