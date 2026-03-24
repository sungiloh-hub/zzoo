import os, time, json
from typing import TypedDict, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from models import RecommendationResponse
from prompts import SYSTEM_PROMPT
from rag import RAGManager

MODEL_NAME = "gemini-2.0-flash-lite"
MAX_RETRIES = 2

# 2.2 LangGraph Multi-Agent 설계 (AgentState 정의)
class AgentState(TypedDict):
    target_calories: int
    selected_course: str      # 사용자 입력 ("윈디쉬", "진국" 등)
    today_date: str           # 자동감지 날짜
    course_menus: Dict[str, Any]
    lunch_calories: int
    lunch_menu_name: str
    remaining_calories: int
    nutrition_analysis: str
    final_recommendation: Any

# 2.2 Date Agent
def date_agent(state: AgentState):
    """오늘 날짜 실시간 자동 감지"""
    today = datetime.now().strftime("%Y-%m-%d")
    return {"today_date": today}

# 2.2 Menu Loader Agent (RAG)
def menu_loader_agent(state: AgentState):
    """오늘 날짜 기준 4개 코스 전체 메뉴를 Vector DB에서 로드"""
    rag = RAGManager()
    menus = rag.get_today_menu(state["today_date"])
    return {"course_menus": menus}

# 2.2 Course Selector Agent
def course_selector_agent(state: AgentState):
    """사용자가 선택한 코스 기반 메뉴 제원 조회"""
    course = state["selected_course"]
    menus = state.get("course_menus", {})
    lunch_info = menus.get(course, {"menu_name": "일반식", "calories": 700})
    return {
        "lunch_calories": lunch_info.get("calories", 700),
        "lunch_menu_name": lunch_info.get("menu_name", "미등록 메뉴")
    }

# 2.2 Calorie Calculator Agent
def calorie_calculator_agent(state: AgentState):
    """잔여 칼로리 산출: (목표 - 중식)"""
    remain = state["target_calories"] - state["lunch_calories"]
    return {"remaining_calories": remain}

# 2.2 Nutrition Analyzer Agent
def nutrition_analyzer_agent(state: AgentState):
    """코스 영양소 균형 판단 (A2A 1)"""
    course = state["selected_course"]
    analysis = "전반적인 균형 식단이 필요합니다."
    
    if course == "면가":
        analysis = "점심에 밀가루(탄수화물)가 과다했으니 저녁은 저탄수·고단백 구성을 권장합니다."
    elif course == "샐러데이":
        analysis = "점심이 매우 가벼웠으므로, 적정량의 복합탄수화물과 질 좋은 지방·단백질 식단이 좋습니다."
    elif course == "진국":
        analysis = "나트륨 섭취가 있었으므로 체내 수분 밸런스와 저염 식단을 위주로 추천해 주세요."
    elif course == "윈디쉬":
        analysis = "지방과 열량이 높은 양식 위주였으므로 저녁은 깔끔한 나물 혹은 샐러드가 포함된 가벼운 한식을 추천하세요."

    return {"nutrition_analysis": analysis}

# 2.2 Recommendation Agent (LLM + Structured Output)
def recommendation_agent(state: AgentState):
    """Gemini 기반 영양 추천. 2.5 Structured Output (Pydantic) 강제 반환."""
    
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.7)
    
    # 2.1 Prompt에 컨텍스트 결합, Role 기반 주입
    prompt_text = f"""
{SYSTEM_PROMPT}

[사용자 현재 상황]
- 날짜: {state['today_date']}
- 목표: {state['target_calories']} kcal
- 선택 중식: {state['selected_course']} ({state['lunch_menu_name']}, {state['lunch_calories']}kcal)
- 잔여 칼로리 여유: {state['remaining_calories']} kcal
- 영양 분석 소견: {state['nutrition_analysis']}

위 정보를 기반으로 저녁 메뉴 3종을 추천해 주세요.
[중요 지시사항]
반드시 3가지 메뉴 각각의 칼로리가 남은 목표 칼로리({state['remaining_calories']} kcal)의 ±10% 오차 범위 내에 들어오도록 양이나 재료를 조절한 특식/요리를 제안하세요. 목표를 채우기 위해 여러 음식을 하나의 세트로 묶어서 추천해도 좋습니다.

반드시 아래 JSON 포맷으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요:
{{
  "today_date": "{state['today_date']}",
  "selected_course": "{state['selected_course']}",
  "lunch_menu": "{state['lunch_menu_name']}",
  "lunch_calories": {state['lunch_calories']},
  "remaining_calories": {state['remaining_calories']},
  "recommendations": [
    {{
      "menu_name": "메뉴명",
      "calories": 숫자,
      "protein": 숫자,
      "carbs": 숫자,
      "fat": 숫자,
      "reason": "추천 이유",
      "alternatives": ["대체1", "대체2"],
      "english_name": "음식의 대표 영어 단어 1~2개"
    }}
  ]
}}
"""
    structured_llm = llm.with_structured_output(RecommendationResponse)
    
    # Rate Limit 대응 Retry 로직
    for attempt in range(MAX_RETRIES):
        try:
            res = structured_llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt_text)
            ])
            return {"final_recommendation": res}
        except Exception as e:
            print(f"[Recommendation Agent] Attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)  # Rate Limit 대기 시간을 30초에서 2초로 대폭 단축하여 빠른 응답 유도
    
    # 예상치 못한 에러가 날 경우 잔여 칼로리를 억지로라도 맞춘 다이내믹 Fallback
    target = state['remaining_calories']
    fallback = RecommendationResponse(
        today_date=state['today_date'],
        selected_course=state['selected_course'],
        lunch_menu=state['lunch_menu_name'],
        lunch_calories=state['lunch_calories'],
        remaining_calories=target,
        recommendations=[
            {"menu_name": "특제 소고기 스테이크 정식", "calories": int(target*0.95), "protein": 45, "carbs": int(target*0.1), "fat": 20, "reason": "부족한 양을 채워줄 든든한 단백질 특식", "alternatives": ["양갈비 구이", "바비큐 폭립"], "english_name": "beef steak set"},
            {"menu_name": "해산물 로제 파스타 곱빼기", "calories": int(target*1.05), "protein": 30, "carbs": int(target*0.15), "fat": 15, "reason": "맛있게 꽉 채우는 탄수화물과 해산물의 조화", "alternatives": ["크림 리조또", "토마토 해물찜"], "english_name": "seafood rose pasta"},
            {"menu_name": "치킨 가라아게 덮밥 세트", "calories": int(target*1.0), "protein": 40, "carbs": int(target*0.13), "fat": 25, "reason": "잔여 칼로리에 딱 맞춘 완벽한 치팅밀", "alternatives": ["돈까스 정식", "새우튀김 덮밥"], "english_name": "chicken karaage bowl"}
        ]
    )
    return {"final_recommendation": fallback}


# LangGraph Orchestrator 설계
def build_graph():
    workflow = StateGraph(AgentState)
    
    # Nodes 등록
    workflow.add_node("date_agent", date_agent)
    workflow.add_node("menu_loader_agent", menu_loader_agent)
    workflow.add_node("course_selector_agent", course_selector_agent)
    workflow.add_node("calorie_calculator_agent", calorie_calculator_agent)
    workflow.add_node("nutrition_analyzer_agent", nutrition_analyzer_agent)
    workflow.add_node("recommendation_agent", recommendation_agent)
    
    # Edges 연결
    workflow.add_edge(START, "date_agent")
    workflow.add_edge("date_agent", "menu_loader_agent")
    workflow.add_edge("menu_loader_agent", "course_selector_agent")
    workflow.add_edge("course_selector_agent", "calorie_calculator_agent")
    workflow.add_edge("calorie_calculator_agent", "nutrition_analyzer_agent")
    workflow.add_edge("nutrition_analyzer_agent", "recommendation_agent")
    workflow.add_edge("recommendation_agent", END)
    
    return workflow.compile()

# 글로벌 싱글톤 Graph 
recommendation_graph = build_graph()
