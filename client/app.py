from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from psi import llm_automation, Linkedin_post
import os
import threading
import time
from datetime import datetime
import json

app = Flask(__name__)

# Configuration
OPENAI_API_KEY = ""
access_token = ""

app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

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
