import sys
from psi import llm_automation, Linkedin_post

OPENAI_API_KEY = ""
access_token = ""

def psi(prompt):
    try:
        llm = llm_automation.llm_auto(prompt, OPENAI_API_KEY)
        if llm.intent_indentifier() == "#Post":
            url = llm.prompt_link_capturer()
            res = Linkedin_post.LinkedinAutomate(access_token, url, OPENAI_API_KEY).main_func()
            return llm.posted_or_not(res)
        else:
            return llm.normal_gpt()
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Example usage
prompt = "create content about my new medium blog post https://medium.com/@gathnex/new-generative-ai-course-by-deeplearning-ai-daf34e24e9c8 and post it on my linkedin"
result = psi(prompt)
print(result)

# Print the Python version and module search path for debugging
print(f"Python version: {sys.version}")
print(f"Module search path: {sys.path}")