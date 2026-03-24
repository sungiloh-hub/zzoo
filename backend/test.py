from dotenv import load_dotenv
load_dotenv()
try:
    from graph import recommendation_graph
    state = {
        'target_calories': 2000,
        'selected_course': '윈디쉬',
        'today_date': '2026-03-24',
        'course_menus': {},
        'lunch_calories': 800,
        'lunch_menu_name': '돈까스',
        'remaining_calories': 1200,
        'nutrition_analysis': '탄수화물 과다'
    }
    res = recommendation_graph.invoke(state)
    print("SUCCESS")
    print(res)
except Exception as e:
    import traceback
    print("FAILED")
    traceback.print_exc()
