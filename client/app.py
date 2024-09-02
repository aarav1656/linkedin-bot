from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from psi import llm_automation, Linkedin_post
import os
import threading
import time
from datetime import datetime
import json
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo, ValidationError

app = Flask(__name__)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configuration
OPENAI_API_KEY = "sk-proj-"
access_token = "---X92hvRrQm7l7bSd8qTTl0T--WXZE8NzrdrPmLhR_mx0q8KsxDgX_8A"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://.com/'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)  # Indicates if the user is an admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AllowedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
# Models
class PromptHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.String(500), nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class ScheduledPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.String(500), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Utility functions
def post_to_linkedin(prompt):
    llm = llm_automation.llm_auto(prompt, OPENAI_API_KEY)
    intent = llm.intent_indentifier()
    
    if intent == "#Post":
        url = llm.prompt_link_capturer()
        linkedin_auto = Linkedin_post.LinkedinAutomate(access_token, url, OPENAI_API_KEY)
        res = linkedin_auto.main_func()
        return llm.posted_or_not(res)
    else:
        return llm.normal_gpt()

def schedule_checker():
    while True:
        now = datetime.now()
        scheduled_posts = ScheduledPost.query.filter(ScheduledPost.scheduled_time <= now).all()
        for post in scheduled_posts:
            result = post_to_linkedin(post.prompt)
            print(f"Posted scheduled content: {result}")
            db.session.delete(post)
        db.session.commit()
        time.sleep(60)  # Check every minute
class SignupForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already in use.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Login')

# Routes
@app.route('/')
def index():
    prompt_history = PromptHistory.query.order_by(PromptHistory.created_at.desc()).all()
    scheduled_posts = ScheduledPost.query.order_by(ScheduledPost.scheduled_time.asc()).all()
    return render_template('index.html', prompt_history=prompt_history, scheduled_posts=scheduled_posts)

@app.route('/post', methods=['POST'])
def handle_post():
    prompt = request.form['prompt']
    scheduled_time = request.form.get('scheduledTime')

    if scheduled_time:
        scheduled_post = ScheduledPost(prompt=prompt, scheduled_time=scheduled_time)
        db.session.add(scheduled_post)
        db.session.commit()
        return jsonify({'success': True, 'message': f"Post scheduled for {scheduled_time}"})
    else:
        try:
            result = post_to_linkedin(prompt)
            # Store the result in the database
            prompt_history = PromptHistory(prompt=prompt, response=result)
            db.session.add(prompt_history)
            db.session.commit()
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

@app.route('/history', methods=['GET'])
def get_history():
    prompt_history = PromptHistory.query.order_by(PromptHistory.created_at.desc()).all()
    history_data = [{'prompt': h.prompt, 'response': h.response, 'created_at': h.created_at} for h in prompt_history]
    return jsonify(history_data)

@app.route('/scheduled', methods=['GET'])
def get_scheduled_posts():
    scheduled_posts = ScheduledPost.query.order_by(ScheduledPost.scheduled_time.asc()).all()
    scheduled_data = [{'prompt': s.prompt, 'scheduled_time': s.scheduled_time} for s in scheduled_posts]
    return jsonify(scheduled_data)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Signup successful. Awaiting admin approval.'})
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.is_approved:
                login_user(user)
                return jsonify({'success': True, 'message': 'Login successful!'})
            else:
                return jsonify({'success': False, 'message': 'Your account is not approved by the admin yet.'})
        else:
            return jsonify({'success': False, 'message': 'Login failed. Check your email and password.'})
    return render_template('login.html', form=form)

@app.route('/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.is_admin:
        if AllowedEmail.query.filter_by(email=user.email).first():
            user.is_approved = True
            db.session.commit()
            return jsonify({'success': True, 'message': f'User {user.email} approved.'})
        else:
            return jsonify({'success': False, 'message': 'This email is not in the allowed list.'})
    return jsonify({'success': False, 'message': 'Unauthorized.'})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/add_allowed_email', methods=['POST'])
@login_required
def add_allowed_email():
    if current_user.is_admin:
        email = request.form.get('email')
        if email:
            allowed_email = AllowedEmail(email=email)
            db.session.add(allowed_email)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Email {email} is now allowed to sign up.'})
    return jsonify({'success': False, 'message': 'Unauthorized.'})

@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email and password:
            user = User(email=email, is_admin=True, is_approved=True)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return "Admin created!"
    return render_template('create_admin.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect('/')

    if request.method == 'POST':
        # Handle approval of users
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            user.is_approved = True
            db.session.commit()

        # Handle adding allowed emails
        allowed_email = request.form.get('allowed_email')
        if allowed_email:
            allowed_user = AllowedEmail(email=allowed_email)
            db.session.add(allowed_user)
            db.session.commit()

    users = User.query.filter_by(is_approved=False).all()
    allowed_emails = AllowedEmail.query.all()
    return render_template('admin_dashboard.html', users=users, allowed_emails=allowed_emails)


# Main entry
if __name__ == '__main__':
    # Create the database tables
    with app.app_context():
        db.create_all()

    # Start the schedule checker thread
    scheduler_thread = threading.Thread(target=schedule_checker)
    scheduler_thread.start()

    # Run the Flask app
    app.run(debug=True)
