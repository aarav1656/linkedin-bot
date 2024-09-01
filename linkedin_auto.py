import sys
from psi import llm_automation, Linkedin_post
# from /Linkedin_post import LinkedinAutomate 
OPENAI_API_KEY = ""
access_token = ""

def psi(prompt):
    try:
        llm = llm_automation.llm_auto(prompt, OPENAI_API_KEY)
        
        intent = llm.intent_indentifier()
        print(f"Identified intent: {intent}")
        
        if intent == "#Post":
            url = llm.prompt_link_capturer()
            print(f"Captured URL: {url}")
            
            # Create LinkedIn automation object
            linkedin_auto = Linkedin_post.LinkedinAutomate(access_token, url, OPENAI_API_KEY)
            
            # Call main_func with error handling
            try:
                res = linkedin_auto.main_func()
                print(f"LinkedIn post result: {res}")
            except Exception as e:
                print(f"Error in LinkedIn posting: {type(e).__name__}: {str(e)}")
                # If there's a response object in the exception, print its content
                if hasattr(e, 'response'):
                    print(f"Response content: {e.response.content}")
                return f"An error occurred while posting to LinkedIn: {str(e)}"
            
            return llm.posted_or_not(res)
        else:
            return llm.normal_gpt()
    except Exception as e:
        return f"An error occurred: {type(e).__name__}: {str(e)}"
# Example usage
prompt = "explain quantam computing https://www.techstars.com/ and post it on linkedin"
result = psi(prompt)
print(result)

# Print the Python version and module search path for debugging
print(f"Python version: {sys.version}")
print(f"Module search path: {sys.path}")