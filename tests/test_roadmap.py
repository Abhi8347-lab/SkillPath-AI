"""
Unit tests for Personalized Learning Roadmap module.
"""
import pytest
from database import init_db, get_all_employees
from modules.roadmap import (
    generate_learning_roadmap,
    create_roadmap_timeline_chart
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(force_reseed=True)


def test_generate_learning_roadmap():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])

    roadmap = generate_learning_roadmap(first_id)
    assert roadmap["employee_id"] == first_id
    assert roadmap["total_courses"] > 0
    assert roadmap["total_hours"] > 0
    assert roadmap["total_weeks"] > 0
    assert len(roadmap["milestones"]) > 0

    # Test sequential pacing: each subsequent milestone starts where previous ended
    milestones = roadmap["milestones"]
    for i in range(len(milestones) - 1):
        assert abs(milestones[i]["end_week"] - milestones[i + 1]["start_week"]) < 0.01


def test_roadmap_phases():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    roadmap = generate_learning_roadmap(first_id)
    
    assert "phases" in roadmap
    assert len(roadmap["phases"]) > 0


def test_roadmap_timeline_chart():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    roadmap = generate_learning_roadmap(first_id)

    fig = create_roadmap_timeline_chart(roadmap)
    assert fig is not None
    assert len(fig.data) == len(roadmap["milestones"])
