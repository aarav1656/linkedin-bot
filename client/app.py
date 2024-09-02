from flask import Flask, render_template, request, jsonify
from psi import llm_automation, Linkedin_post
import os

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
LINKEDIN_ACCESS_TOKEN = os.environ.get('LINKEDIN_ACCESS_TOKEN')

SCHEDULE_FILE = 'scheduled_posts.json'

def load_scheduled_posts():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_scheduled_posts(posts):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(posts, f)

def post_to_linkedin(prompt):
    llm = llm_automation.llm_auto(prompt, OPENAI_API_KEY)
    intent = llm.intent_indentifier()
    
    if intent == "#Post":
        url = llm.prompt_link_capturer()
        linkedin_auto = Linkedin_post.LinkedinAutomate(LINKEDIN_ACCESS_TOKEN, url, OPENAI_API_KEY)
        res = linkedin_auto.main_func()
        return llm.posted_or_not(res)
    else:
        return llm.normal_gpt()

def schedule_checker():
    while True:
        now = datetime.now()
        scheduled_posts = load_scheduled_posts()
        for post in scheduled_posts:
            scheduled_time = datetime.fromisoformat(post['scheduled_time'])
            if now >= scheduled_time:
                result = post_to_linkedin(post['prompt'])
                print(f"Posted scheduled content: {result}")
                scheduled_posts.remove(post)
        save_scheduled_posts(scheduled_posts)
        time.sleep(60)  # Check every minute

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def handle_post():
    prompt = request.form['prompt']
    scheduled_time = request.form.get('scheduledTime')

    if scheduled_time:
        scheduled_posts = load_scheduled_posts()
        scheduled_posts.append({
            'prompt': prompt,
            'scheduled_time': scheduled_time
        })
        save_scheduled_posts(scheduled_posts)
        return jsonify({'success': True, 'message': f"Post scheduled for {scheduled_time}"})
    else:
        try:
            result = post_to_linkedin(prompt)
            return jsonify({'success': True, 'message': result})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=schedule_checker)
    scheduler_thread.start()
    app.run(debug=True)