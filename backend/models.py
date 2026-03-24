from pydantic import BaseModel, Field
from typing import List

# 2.5 Structured Output 강제를 위한 Pydantic 스키마 정의
class RecommendationItem(BaseModel):
    menu_name: str = Field(description="추천 저녁 메뉴명")
    calories: int = Field(description="해당 메뉴의 칼로리 (숫자)")
    protein: int = Field(description="단백질 제공량(g)")
    carbs: int = Field(description="탄수화물 제공량(g)")
    fat: int = Field(description="지방 제공량(g)")
    reason: str = Field(description="이 메뉴를 추천하는 상세한 이유 (영양소 잔여량, 낮 메뉴 기반)")
    alternatives: List[str] = Field(description="유사한 대체 메뉴 옵션 리스트")
    english_name: str = Field(default="", description="음식의 대표적인 영어 명칭 (예: salmon salad, beef steak)")

class RecommendationResponse(BaseModel):
    today_date: str = Field(description="입력된 오늘 날짜")
    selected_course: str = Field(description="사용자가 선택한 코스 (윈디쉬/진국/면가/샐러데이 중)")
    lunch_menu: str = Field(description="선택한 코스의 실제 중식 메뉴명")
    lunch_calories: int = Field(description="선택 코스의 칼로리")
    remaining_calories: int = Field(description="잔여 목표 칼로리 (목표 - 중식)")
    recommendations: List[RecommendationItem] = Field(description="3가지 저녁 추천 메뉴 배열")
