from dotenv import load_dotenv
import os
import requests

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)
if response.status_code == 200:
    models = response.json().get('models', [])
    for m in models:
        if 'gemini' in m['name']:
            print(m['name'])
else:
    print("Error:", response.status_code, response.text)
