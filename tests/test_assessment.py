"""
Unit tests for employee assessment module.
"""
import pytest
from database import init_db, get_employee_by_id, get_employee_skills
from modules.assessment import (
    validate_employee_input,
    validate_proficiency_level,
    save_or_update_employee,
    save_employee_skill_assessment,
    score_diagnostic_quiz
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(force_reseed=True)


def test_validate_employee_input():
    # Valid
    ok, err = validate_employee_input("John Doe", "john@example.com", "Engineering", "Dev", "Lead", 4.0, 5.0)
    assert ok is True
    assert err is None

    # Invalid email
    ok, err = validate_employee_input("John Doe", "not-an-email", "Engineering", "Dev", "Lead", 4.0, 5.0)
    assert ok is False
    assert "email" in err.lower()

    # Invalid hours
    ok, err = validate_employee_input("John Doe", "john@example.com", "Engineering", "Dev", "Lead", 4.0, 50.0)
    assert ok is False
    assert "hours" in err.lower()

    # Invalid experience
    ok, err = validate_employee_input("John Doe", "john@example.com", "Engineering", "Dev", "Lead", -2.0, 5.0)
    assert ok is False
    assert "experience" in err.lower()


def test_validate_proficiency_level():
    assert validate_proficiency_level(1) is True
    assert validate_proficiency_level(5) is True
    assert validate_proficiency_level(0) is False
    assert validate_proficiency_level(6) is False
    assert validate_proficiency_level("3") is False


def test_create_and_update_employee():
    # Create new
    emp_id, err = save_or_update_employee(
        name="Test Candidate",
        email="candidate.test@domain.com",
        department="Engineering",
        current_role="Junior Engineer",
        target_role="AI / ML Engineer",
        experience_years=1.0,
        weekly_learning_hours=6.0
    )
    assert err is None
    assert emp_id is not None

    # Verify stored
    emp = get_employee_by_id(emp_id)
    assert emp["name"] == "Test Candidate"

    # Update existing
    updated_id, err = save_or_update_employee(
        name="Test Candidate Updated",
        email="candidate.test@domain.com",
        department="Engineering",
        current_role="Junior Engineer",
        target_role="AI / ML Engineer",
        experience_years=2.0,
        weekly_learning_hours=8.0,
        employee_id=emp_id
    )
    assert err is None
    assert updated_id == emp_id
    emp_updated = get_employee_by_id(emp_id)
    assert emp_updated["name"] == "Test Candidate Updated"
    assert emp_updated["experience_years"] == 2.0


def test_save_employee_skill_assessment():
    from database import get_all_skills
    skills_df = get_all_skills()
    s1_id = int(skills_df.iloc[0]["id"])
    s2_id = int(skills_df.iloc[1]["id"])

    emp_id, _ = save_or_update_employee(
        name="Assessed Person",
        email="assessed.person@domain.com",
        department="Data & Analytics",
        current_role="Analyst",
        target_role="Data Scientist",
        experience_years=2.0,
        weekly_learning_hours=5.0
    )
    # Save ratings with valid skill IDs
    ratings = {s1_id: 4, s2_id: 3}
    success, err = save_employee_skill_assessment(emp_id, ratings)
    assert success is True
    assert err is None

    skills = get_employee_skills(emp_id)
    s1 = skills[skills["skill_id"] == s1_id].iloc[0]
    assert s1["proficiency_level"] == 4


def test_score_diagnostic_quiz():
    # Perfect score test
    perfect_answers = {1: 1, 2: 1, 3: 1, 4: 1, 5: 0, 6: 1}
    res = score_diagnostic_quiz(perfect_answers)
    assert res["correct_answers"] == 6
    assert res["score_pct"] == 100.0
    assert res["suggested_baseline"] == 4

    # Zero score
    zero_answers = {1: 0, 2: 0, 3: 0, 4: 0, 5: 2, 6: 0}
    res_zero = score_diagnostic_quiz(zero_answers)
    assert res_zero["correct_answers"] == 0
    assert res_zero["suggested_baseline"] == 1
