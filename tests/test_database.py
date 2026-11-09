"""
Unit tests for database schema, initialization, and queries.
"""
import pytest
from database import (
    init_db,
    get_all_employees,
    get_employee_by_id,
    get_all_skills,
    get_role_requirements,
    get_all_courses,
    get_employee_skills
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Ensure database is initialized and seeded before running tests."""
    init_db(force_reseed=True)


def test_init_db_seeds_employees():
    employees_df = get_all_employees()
    assert len(employees_df) >= 10
    assert "Aarav Sharma" in employees_df["name"].values
    assert "email" in employees_df.columns
    assert "target_role" in employees_df.columns


def test_get_employee_by_id():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    emp = get_employee_by_id(first_id)
    assert emp is not None
    assert emp["name"] == "Aarav Sharma"
    assert emp["department"] == "Engineering"


def test_skills_catalog():
    skills_df = get_all_skills()
    assert len(skills_df) >= 15
    skill_names = set(skills_df["name"].values)
    assert "Python Programming" in skill_names
    assert "Machine Learning" in skill_names
    assert "AWS Cloud Architecture" in skill_names


def test_role_requirements():
    reqs = get_role_requirements("AI / ML Engineer")
    assert not reqs.empty
    assert len(reqs) >= 4
    skill_names = set(reqs["skill_name"].values)
    assert "Python Programming" in skill_names
    assert "Machine Learning" in skill_names


def test_courses_catalog_and_urls():
    courses_df = get_all_courses()
    assert len(courses_df) >= 15
    # Verify all courses have valid platforms and URLs
    for _, course in courses_df.iterrows():
        url = course["platform_url"]
        assert url.startswith("http://") or url.startswith("https://")
        assert len(course["title"]) > 3
        assert 1 <= course["level"] <= 5
        assert course["rating"] > 0


def test_employee_skills_retrieval():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    emp_skills = get_employee_skills(first_id)
    assert not emp_skills.empty
    # Aarav Sharma should have Python level 3
    py_row = emp_skills[emp_skills["skill_name"] == "Python Programming"]
    assert not py_row.empty
    assert py_row.iloc[0]["proficiency_level"] == 3
