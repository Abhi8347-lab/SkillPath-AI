"""
Unit tests for course recommendation engine.
"""
import pytest
from database import init_db, get_all_employees
from modules.recommender import (
    calculate_difficulty_fit,
    calculate_duration_fit,
    recommend_courses
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(force_reseed=True)


def test_difficulty_fit():
    assert calculate_difficulty_fit(2, 3) == 100.0   # +1 level is optimal
    assert calculate_difficulty_fit(2, 2) == 70.0    # Same level
    assert calculate_difficulty_fit(3, 1) == 25.0    # Lower level


def test_duration_fit():
    assert calculate_duration_fit(20.0, 5.0) == 100.0   # 4 weeks -> sweet spot
    assert calculate_duration_fit(100.0, 5.0) == 50.0   # 20 weeks -> too long


def test_recommend_courses_ai_heuristic():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    
    recs = recommend_courses(first_id, top_n=5, use_ai_heuristic=True)
    assert len(recs) > 0
    assert len(recs) <= 5
    
    # Check top recommendation properties
    top = recs[0]
    assert "title" in top
    assert "platform_url" in top
    assert top["platform_url"].startswith("http")
    assert "score" in top
    assert top["score"] > 0
    assert "explanation" in top
    assert len(top["explanation"]) > 5


def test_recommend_courses_deterministic_fallback():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    
    recs = recommend_courses(first_id, top_n=5, use_ai_heuristic=False)
    assert len(recs) > 0
    # Top course in fallback should have a positive gap
    assert recs[0]["gap"] >= 0


def test_recommend_courses_with_skill_filter():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    
    # Fetch first recommendation to get its skill_id
    all_recs = recommend_courses(first_id, top_n=1)
    target_skill_id = all_recs[0]["skill_id"]
    
    filtered_recs = recommend_courses(first_id, filter_skill_id=target_skill_id)
    assert len(filtered_recs) > 0
    for r in filtered_recs:
        assert r["skill_id"] == target_skill_id
