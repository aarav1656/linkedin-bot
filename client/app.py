from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import threading
from datetime import datetime
import time
from flask_wtf import CSRFProtect


# Initialize Flask app
app = Flask(__name__)

# Configuration
OPENAI_API_KEY = "sk-proj-"
access_token = "--8Cj3KS7i0QFnXisvXyAZxPiOKLCLjIN9ItlqwjuYQvHJ85WAOW0K80vn4nUStQp_Kol8BZRnqGayys1uodH0o5_tOgbHJRcP1UpA8pLpKF121OzNWBzKsVnTDKDSBlx0QLO7-X92hvRrQm7l7bSd8qTTl0T-4Xlu2hDHNPztD8d3iYS8XnKmQTVMQZMZ-WXZE8NzrdrPmLhR_mx0q8KsxDgX_8A"

app.config['SECRET_KEY'] = "5"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://:@kala...com/xaqptoyj'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)
login_manager.login_view = 'login'

# Import routes after initializing app
from routes import *

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

if __name__ == '__main__':
    # Create the database tables
    with app.app_context():
        db.create_all()

    # Start the schedule checker thread
    scheduler_thread = threading.Thread(target=schedule_checker)
    scheduler_thread.start()

    # Run the Flask app
    app.run(debug=True)
