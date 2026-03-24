import os, time, json
from typing import TypedDict, Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools import DuckDuckGoSearchResults
from pydantic import BaseModel, Field
from models import RecommendationResponse
from prompts import SYSTEM_PROMPT
from rag import RAGManager

MODEL_NAME = "gemini-2.5-flash"
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
    latitude: float
    longitude: float
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
    
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.7, max_retries=0)
    
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
1. 반드시 **서로 완전히 다른 3가지 종류**의 저녁 메뉴를 추천해야 합니다. (절대로 같은 메뉴를 2개 이상 중복해서 출력하지 마세요!)
2. 3가지 메뉴 각각의 칼로리가 남은 목표 칼로리({state['remaining_calories']} kcal)의 ±10% 오차 범위 내에 들어오도록 양이나 재료를 조절한 특식/요리를 제안하세요. 목표를 채우기 위해 여러 음식을 하나의 세트로 묶어서 추천해도 좋습니다.

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
      "english_name": "해당 요리의 핵심 식재료를 나타내는 영어 단어 딱 1개. loremflickr.com에서 검색 가능한 일반적인 영어 단어여야 합니다. (예: chicken, beef, salmon, rice, noodle, salad)"
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
            err_msg = str(e)
            print(f"[Recommendation Agent] Attempt {attempt+1}/{MAX_RETRIES} failed: {err_msg}")
            
            # API 키 오류나 할당량 초과(429) 등은 재시도 없이 즉시 에러를 발생시킴
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                raise Exception("구글 AI API 키 할당량이 전부 소진되었습니다 (429 RESOURCE_EXHAUSTED). 새로운 키가 필요합니다.")
            if "API_KEY_INVALID" in err_msg or "400" in err_msg or "403" in err_msg:
                raise Exception("구글 AI API 키가 올바르지 않거나 권한이 없습니다.")
                
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)  # Rate Limit 대기 시간을 30초에서 2초로 대폭 단축하여 빠른 응답 유도
            else:
                raise Exception(f"AI 추천을 생성하지 못했습니다. (원인: {err_msg})")


# 2.2 Restaurant Search Agent (DuckDuckGo Local Search Tool)
def restaurant_search_agent(state: AgentState):
    """추천된 메뉴 정보를 받아 실제 식당을 DuckDuckGo로 검색하여 결과를 병합"""
    recommendations = state.get("final_recommendation")
    if not hasattr(recommendations, "recommendations"):
        return {"final_recommendation": recommendations}

    # Tool Setting
    search_tool = DuckDuckGoSearchResults()
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.1, max_retries=1)
    
    for rec in recommendations.recommendations:
        try:
            # 사용자의 위도, 경도가 실제 값이면 쿼리에 포함하여 검색 정밀도 향상
            loc_context = ""
            if state.get("latitude") and state.get("longitude"):
                # DuckDuckGo는 좌표보다는 지역명에 더 민감하지만 'near [coord]' 형태도 도움을 줌
                loc_context = f"near {state['latitude']}, {state['longitude']}"
            
            # 보다 실질적인 맛집 검색 쿼리 생성
            query = f"{rec.menu_name} 맛집 {loc_context}".strip()
            search_result = search_tool.invoke(query)
            
            prompt = f"""
            검색어: {query}
            사용자 현재 위치(위도,경도): {state.get('latitude')}, {state.get('longitude')}
            검색 결과:
            {search_result}
            
            당신은 위 검색 결과를 분석하여, 사용자의 현재 위치에서 가장 가깝거나 방문하기 좋은 실제 식당 정보를 추출하는 전문가입니다.
            반드시 아래 조건에 맞춰 상호명을 1개 선정하세요.
            1. 실제로 주소나 특징이 명확히 언급된 곳을 우선합니다. 
            2. 검색 결과에 적절한 식당이 없다면 빈 문자열("")을 반환하세요.
            3. restaurant_info에는 거리(알 수 있다면)나 대표 메뉴, 짧은 추천 이유를 평어체(~임, ~함)로 적어주세요.
            """
            
            class RestaurantInfo(BaseModel):
                restaurant_name: str = Field(description="실제 식당 상호명. 못 찾았으면 빈 문자열")
                restaurant_info: str = Field(description="위치 특징이나 선택 이유 등 50자 내외 설명")
            
            structured_llm = llm.with_structured_output(RestaurantInfo)
            res = structured_llm.invoke([HumanMessage(content=prompt)])
            
            rec.restaurant_name = res.restaurant_name
            rec.restaurant_info = res.restaurant_info
            print(f"[Restaurant Finder] Local Search for '{query}': {rec.restaurant_name}")
            
        except Exception as e:
            print(f"[Restaurant Finder] Search Failed for {rec.menu_name}: {e}")
            rec.restaurant_name = ""
            rec.restaurant_info = ""

    return {"final_recommendation": recommendations}

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
    workflow.add_node("restaurant_search_agent", restaurant_search_agent)
    
    # Edges 연결
    workflow.add_edge(START, "date_agent")
    workflow.add_edge("date_agent", "menu_loader_agent")
    workflow.add_edge("menu_loader_agent", "course_selector_agent")
    workflow.add_edge("course_selector_agent", "calorie_calculator_agent")
    workflow.add_edge("calorie_calculator_agent", "nutrition_analyzer_agent")
    workflow.add_edge("nutrition_analyzer_agent", "recommendation_agent")
    workflow.add_edge("recommendation_agent", "restaurant_search_agent")
    workflow.add_edge("restaurant_search_agent", END)
    
    return workflow.compile()

# 글로벌 싱글톤 Graph 
recommendation_graph = build_graph()
