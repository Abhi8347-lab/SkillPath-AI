"""
End-to-end integration test validating the entire employee upskilling lifecycle.
"""
import pytest
from database import init_db, get_employee_by_id, get_employee_skills
from modules.assessment import save_or_update_employee, save_employee_skill_assessment
from modules.skill_gap import analyze_skill_gap
from modules.recommender import recommend_courses
from modules.roadmap import generate_learning_roadmap
from modules.tracker import (
    enroll_employee_in_course,
    log_learning_activity,
    update_course_progress,
    get_employee_tracker_summary
)
from modules.analytics import get_workforce_overview


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(force_reseed=True)


def test_full_employee_lifecycle():
    # 1. Register new employee
    emp_id, err = save_or_update_employee(
        name="Karan Johar",
        email="karan.johar@enterprise.org",
        department="Engineering",
        current_role="Junior Developer",
        target_role="AI / ML Engineer",
        experience_years=1.5,
        weekly_learning_hours=6.0
    )
    assert err is None
    assert emp_id is not None

    # 2. Assess skills (initially low in AI/ML skills)
    from database import get_all_skills
    skills_df = get_all_skills()
    py_id = int(skills_df[skills_df["name"] == "Python Programming"].iloc[0]["id"])
    ml_id = int(skills_df[skills_df["name"] == "Machine Learning"].iloc[0]["id"])
    
    ratings = {py_id: 2, ml_id: 1}
    success, s_err = save_employee_skill_assessment(emp_id, ratings)
    assert success is True
    assert s_err is None

    # 3. Analyze skill gap
    gap_res = analyze_skill_gap(emp_id)
    assert gap_res["readiness_score"] < 50.0  # Should be low readiness initially
    assert len(gap_res["critical_gaps"]) >= 1

    # 4. Generate recommendations
    recs = recommend_courses(emp_id, top_n=3, use_ai_heuristic=True)
    assert len(recs) >= 1
    top_course = recs[0]
    top_course_id = top_course["course_id"]
    initial_readiness = gap_res["readiness_score"]

    # 5. Generate roadmap
    roadmap = generate_learning_roadmap(emp_id)
    assert roadmap["total_courses"] >= 1
    assert roadmap["total_hours"] > 0

    # 6. Enroll and log progress
    enrolled, e_err = enroll_employee_in_course(emp_id, top_course_id)
    assert enrolled is True

    # Log 5 hours study session
    logged, l_err = log_learning_activity(emp_id, top_course_id, 5.0, "Studied algorithms.")
    assert logged is True

    # 7. Complete course to 100% -> triggers auto skill level up!
    completed, c_err, notif = update_course_progress(emp_id, top_course_id, 100)
    assert completed is True
    assert notif is not None
    assert "completed" in notif.lower()

    # Verify skill was elevated
    emp_skills = get_employee_skills(emp_id)
    skill_elevated = emp_skills[emp_skills["skill_id"] == top_course["skill_id"]].iloc[0]
    assert skill_elevated["proficiency_level"] >= top_course["level"]

    # 8. Re-evaluate skill gap -> readiness score must increase!
    new_gap_res = analyze_skill_gap(emp_id)
    assert new_gap_res["readiness_score"] >= initial_readiness

    # 9. Verify Tracker Summary reflects badges & hours
    tracker_summary = get_employee_tracker_summary(emp_id)
    assert tracker_summary["completed_courses"] == 1
    assert tracker_summary["total_hours"] >= 5.0
    assert len(tracker_summary["badges"]) >= 2

    # 10. Verify HR Workforce Overview includes the new employee and training stats
    wf_overview = get_workforce_overview()
    assert wf_overview["total_employees"] >= 11
    assert wf_overview["overall_training_hours"] >= 5.0
