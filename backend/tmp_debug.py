import os, sys, traceback
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

print("=== Step 1: ENV check ===")
key = os.getenv("GOOGLE_API_KEY")
print(f"GOOGLE_API_KEY: {key[:10]}..." if key else "KEY NOT FOUND!")

print("\n=== Step 2: LLM test ===")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    res = llm.invoke([HumanMessage(content="Say hello in Korean, one sentence only.")])
    print(f"LLM Response: {res.content}")
except Exception as e:
    traceback.print_exc()

print("\n=== Step 3: Full graph test ===")
try:
    from graph import recommendation_graph
    result = recommendation_graph.invoke({"target_calories": 2000, "selected_course": "윈디쉬"})
    print(f"Graph result keys: {result.keys()}")
    fr = result.get("final_recommendation")
    print(f"Final recommendation type: {type(fr)}")
    if fr:
        print(fr.model_dump() if hasattr(fr, 'model_dump') else fr)
except Exception as e:
    traceback.print_exc()
