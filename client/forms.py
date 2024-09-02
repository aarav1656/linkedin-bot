from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo, ValidationError
from models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already in use.')

    def create_user(self):
        hashed_password = bcrypt.generate_password_hash(self.password.data).decode('utf-8')
        user = User(email=self.email.data, password_hash=hashed_password)
        return user

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

    def validate_login(self):
        user = User.query.filter_by(email=self.email.data).first()
        if not user or not bcrypt.check_password_hash(user.password_hash, self.password.data):
            raise ValidationError('Invalid email or password.')
        return user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo, ValidationError
from models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already in use.')

    def create_user(self):
        hashed_password = bcrypt.generate_password_hash(self.password.data).decode('utf-8')
        user = User(email=self.email.data, password_hash=hashed_password)
        return user

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

    def validate_login(self):
        user = User.query.filter_by(email=self.email.data).first()
        if not user or not bcrypt.check_password_hash(user.password_hash, self.password.data):
            raise ValidationError('Invalid email or password.')
        return user
