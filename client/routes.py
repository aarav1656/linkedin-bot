from flask import request, jsonify, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, bcrypt, login_manager
from models import User, AllowedEmail, PromptHistory, ScheduledPost
from forms import SignupForm, LoginForm


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
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
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Create a new user and add to the database
        user = User(email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        # Return success response
        return jsonify({'success': True, 'message': 'Signup successful. Awaiting admin approval.'})
    
    elif request.method == 'POST':
        # Collect error messages from the form
        errors = form.errors
        error_messages = [f"{field}: {', '.join(messages)}" for field, messages in errors.items()]
        
        # Return failure response with specific error messages
        return jsonify({'success': False, 'message': 'Signup failed. Please correct the errors.', 'errors': error_messages})
    
    return render_template('signup.html', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
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
        email = request.form.get('email')
        password = request.form.get('password')

        if email and password:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(email=email, password_hash=hashed_password, is_admin=True, is_approved=True)
            db.session.add(user)
            db.session.commit()
            return "Admin created!"
        return "Failed to create admin. Please provide both email and password."

    return render_template('create_admin.html')


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect('/')

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            user.is_approved = True
            db.session.commit()

        allowed_email = request.form.get('allowed_email')
        if allowed_email:
            allowed_user = AllowedEmail(email=allowed_email)
            db.session.add(allowed_user)
            db.session.commit()

    users = User.query.filter_by(is_approved=False).all()
    allowed_emails = AllowedEmail.query.all()
    return render_template('admin_dashboard.html', users=users, allowed_emails=allowed_emails)
