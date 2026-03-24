from dotenv import load_dotenv
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

models = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-001",
    "gemini-2.5-flash"
]

for m in models:
    try:
        print(f"Testing {m}...")
        llm = ChatGoogleGenerativeAI(model=m, temperature=0.7, max_retries=0)
        res = llm.invoke([HumanMessage(content="Hello")])
        print(f"SUCCESS {m}: {res.content[:20]}")
    except Exception as e:
        print(f"FAIL {m}: {str(e)}")
    time.sleep(2)
