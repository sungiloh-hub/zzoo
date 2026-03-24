from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from graph import recommendation_graph
from rag import RAGManager
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Calorie-Based Dinner AI Agent")

# CORS 방어 완화 (개발용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendRequest(BaseModel):
    target_calories: int
    selected_course: str
    latitude: float = 0.0
    longitude: float = 0.0

@app.get("/")
def read_root():
    """Render 클라우드 Health Check(상태 확인) 및 기본 루트"""
    return {"status": "ok", "message": "Calorie AI Backend is running securely!"}

@app.get("/api/menu/today")
def get_today_menu():
    """오늘 날짜를 감지하고, RAG에서 4개 코스의 메뉴 정보를 반환"""
    today = datetime.now().strftime("%Y-%m-%d")
    rag = RAGManager()
    menus = rag.get_today_menu(today)
    return {
        "today_date": today,
        "menus": menus
    }

@app.post("/api/recommend")
def generate_recommendation(req: RecommendRequest):
    """목표칼로리와 선택코스를 받아 LangGraph 멀티에이전트 실행 후 반환"""
    try:
        inputs = {
            "target_calories": req.target_calories,
            "selected_course": req.selected_course,
            "latitude": req.latitude,
            "longitude": req.longitude
        }
        
        # 2.2 LangGraph 파이프라인 트리거
        result = recommendation_graph.invoke(inputs)
        
        # 2.5 Structured Output (Pydantic 딕셔너리) 직렬화
        response_data = result["final_recommendation"].model_dump()
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
