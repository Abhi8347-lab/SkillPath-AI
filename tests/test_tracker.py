"""
Unit tests for Learning Progress Tracker module.
"""
import pytest
from database import init_db, get_all_employees, get_all_courses, get_employee_skills
from modules.tracker import (
    enroll_employee_in_course,
    update_course_progress,
    log_learning_activity,
    get_employee_tracker_summary
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(force_reseed=True)


def test_enroll_employee_in_course():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    courses_df = get_all_courses()
    course_id = int(courses_df.iloc[4]["id"])

    # First enrollment
    ok, err = enroll_employee_in_course(first_id, course_id)
    assert ok is True
    assert err is None

    # Duplicate enrollment should be rejected
    ok2, err2 = enroll_employee_in_course(first_id, course_id)
    assert ok2 is False
    assert "already enrolled" in err2


def test_update_progress_and_skill_level_up():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    courses_df = get_all_courses()
    course = courses_df.iloc[3]
    course_id = int(course["id"])
    skill_id = int(course["skill_id"])

    # Ensure enrolled
    enroll_employee_in_course(first_id, course_id)

    # Update to 50%
    ok, err, notif = update_course_progress(first_id, course_id, 50)
    assert ok is True
    assert notif is None

    # Update to 100% -> should trigger level up notification
    ok100, err100, notif100 = update_course_progress(first_id, course_id, 100)
    assert ok100 is True
    assert notif100 is not None
    assert "completed" in notif100.lower()

    # Verify skill elevated in employee_skills table
    skills = get_employee_skills(first_id)
    skill_row = skills[skills["skill_id"] == skill_id].iloc[0]
    assert skill_row["proficiency_level"] >= course["level"]


def test_log_learning_activity():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    courses_df = get_all_courses()
    course_id = int(courses_df.iloc[0]["id"])

    # Valid log
    ok, err = log_learning_activity(first_id, course_id, 2.5, "Covered recursion and lists.")
    assert ok is True
    assert err is None

    # Invalid hours
    ok_inv, err_inv = log_learning_activity(first_id, course_id, -1.0)
    assert ok_inv is False


def test_get_employee_tracker_summary():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])

    summary = get_employee_tracker_summary(first_id)
    assert summary["employee_id"] == first_id
    assert summary["total_enrollments"] >= 1
    assert "badges" in summary
    assert isinstance(summary["badges"], list)
