from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

load_dotenv()

try:
    llm1 = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.7)
    res = llm1.invoke([HumanMessage(content="Hello")])
    print("SUCCESS gemini-2.0-flash-lite")
except Exception as e:
    print("FAIL 1:", str(e))

try:
    llm2 = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash-lite", temperature=0.7)
    res = llm2.invoke([HumanMessage(content="Hello")])
    print("SUCCESS models/gemini-2.0-flash-lite")
except Exception as e:
    print("FAIL 2:", str(e))
