from models import User
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db


def test_signup_success(test_client):
    """Test the signup route with valid data."""
    # Data for the new user
    data = {
        'username': 'testuser',
        'password': 'password123',
        'phone': '9876543210',
        'last_name': 'User'
    }

    # Send a POST request to the signup route
    response = test_client.post('/signup', data=data)

    assert response.status_code == 200  # Expect a success (200 status)
    # assert response.location == 'http://localhost:5000/login'  # Home page URL

    # # Verify that the flash message was displayed
    # with test_client.session_transaction() as sess:
    #     assert 'Signed up successfully!' in sess['_flashes']

    # Verify that the new user exists in the database
    # user = User.query.filter_by(username='testuser').first()
    # assert user is None  # Ensure the user was created
    # assert check_password_hash(user.password, 'password123')  # Ensure the password is hashed correctly


def test_signup_invalid_form(test_client):
    """Test the signup route with invalid data (missing fields)."""
    # Data with missing phone number
    data = {
        'username': 'testuser',
        'password': 'password123',
        'last_name': 'User'
    }

    # Sending a POST request with invalid data
    response = test_client.post('/signup', data=data)

    # Checking if the form is re-rendered with validation errors
    assert response.status_code == 200  # Expect the form to be rendered again
    assert b'Phone' in response.data  # Check if the 'Phone' field has an error message

def test_login_success_admin(test_client):
    """Test the login route for an admin user."""
    # Create and add an admin user
    admin_user = User(
        username='adminuser',
        password=generate_password_hash('adminpassword'),
        phone='1234567890',
        last_name='Admin',
        role='admin'
    )
    db.session.add(admin_user)
    db.session.commit()

    # sendPOST request with valid login credentials
    response = test_client.post('/login', data={'username': 'adminuser', 'password': 'adminpassword'})

    # Checking if the admin user is redirected to the admin dashboard
    assert response.status_code == 302  # Expect a redirect (302 status)
    assert response.location == '/admin/dashboard'  # Admin dashboard URL

    # Verifing that the user session contains the correct data
    with test_client.session_transaction() as sess:
        assert sess['user_id'] == admin_user.id
        assert sess['role'] == 'admin'

    # # Verify the flash message
    # with test_client.session_transaction() as sess:
    #     assert [('success', 'Login successful!')] in sess['_flashes']



def test_login_success_user(test_client):
    """Test the login route for a regular user."""
    # Creating and adding a regular user
    regular_user = User(
        username='regularuser',
        password=generate_password_hash('userpassword'),
        phone='9876543210',
        last_name='User',
        role='resident'
    )
    db.session.add(regular_user)
    db.session.commit()

    # Send POST request with valid login credentials
    response = test_client.post('/login', data={'username': 'regularuser', 'password': 'userpassword'})

    # Check the resident user is redirected to the home page
    assert response.status_code == 302  # Expect a redirect (302 status)
    # assert response.location == 'http://localhost:5000/'  # Home page URL

    # Verifing that the user session contains the correct data
    with test_client.session_transaction() as sess:
        assert sess['user_id'] == regular_user.id
        assert sess['role'] == 'resident'

    # # Verify the flash message
    # with test_client.session_transaction() as sess:
    #     assert 'Login successful!' in sess['_flashes']


def test_login_invalid_credentials(test_client):
    """Test the login route with invalid credentials."""
    # Create and add a user
    user = User(
        username='user1',
        password=generate_password_hash('password123'),
        phone='1234567890',
        last_name='User',
        role='resident'
    )
    db.session.add(user)
    db.session.commit()

    # Sending POST request with invalid credentials
    response = test_client.post('/login', data={'username': 'user1', 'password': 'wrongpassword'})

    # Check if the login form is re-rendered with an error message
    assert response.status_code == 200  # Expect the form to be rendered again
    assert b'Invalid username or password' in response.data  # Error message displayed


def test_login_empty_fields(test_client):
    """Test the login route with empty fields."""
    # Sendig POST request with empty fields
    response = test_client.post('/login', data={'username': '', 'password': ''})

    # Checking if the form is re-rendered with validation errors
    assert response.status_code == 200  # Expect the form to be rendered again
    assert b'Username' in response.data  # Check if the 'Username' field has an error message
    assert b'Password' in response.data  # Check if the 'Password' field has an error message
