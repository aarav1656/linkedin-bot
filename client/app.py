from flask import Flask, render_template, request, jsonify
from psi import llm_automation, Linkedin_post
import os

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
LINKEDIN_ACCESS_TOKEN = os.environ.get('LINKEDIN_ACCESS_TOKEN')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def post_to_linkedin():
    prompt = request.form['prompt']
    try:
        llm = llm_automation.llm_auto(prompt, OPENAI_API_KEY)
        intent = llm.intent_indentifier()
        
        if intent == "#Post":
            url = llm.prompt_link_capturer()
            linkedin_auto = Linkedin_post.LinkedinAutomate(LINKEDIN_ACCESS_TOKEN, url, OPENAI_API_KEY)
            res = linkedin_auto.main_func()
            result = llm.posted_or_not(res)
        else:
            result = llm.normal_gpt()
        
        return jsonify({'success': True, 'message': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)