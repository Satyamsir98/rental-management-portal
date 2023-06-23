from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo , Regexp
from flask_wtf.csrf import CSRFProtect

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=80)], render_kw={"class": "form-control"})
    # Phone Field with Validation (Only digits, length of 10)
    phone = StringField('Phone Number', validators=[
        DataRequired(), 
        Length(min=10, max=10, message="Phone number must be 10 digits."),
        Regexp(r'^\d{10}$', message="Phone number must contain only digits.")], 
        render_kw={"class": "form-control"})
    # Last Name Field with Alphabet-only Validation
    last_name = StringField('Last Name', validators=[
        DataRequired(), 
        Length(min=1, max=50), 
        Regexp(r'^[A-Za-z]+$', message="Last name must only contain alphabets.")], 
        render_kw={"class": "form-control"})
    # Password Fields
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)], render_kw={"class": "form-control"})
    # Confirm Password with EqualTo validator
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords must match.")], 
        render_kw={"class": "form-control"})
    # Submit Button
    submit = SubmitField('Sign Up', render_kw={"class": "btn btn-primary"})

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"class": "form-control"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "form-control"})
    submit = SubmitField('Login', render_kw={"class": "btn btn-primary"})

