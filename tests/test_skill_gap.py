"""
Unit tests for Skill Gap Analyzer module.
"""
import pytest
from database import init_db, get_all_employees
from modules.skill_gap import (
    analyze_skill_gap,
    create_radar_chart,
    create_gap_bar_chart
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(force_reseed=True)


def test_analyze_skill_gap_for_seeded_employee():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    
    result = analyze_skill_gap(first_id)
    assert result["employee_id"] == first_id
    assert result["readiness_score"] > 0
    assert result["readiness_score"] <= 100
    assert "gap_df" in result
    assert not result["gap_df"].empty
    assert "critical_gaps" in result
    assert "strengths" in result


def test_gap_analysis_calculations():
    # Test that gap is non-negative and correctly categorized
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    result = analyze_skill_gap(first_id)
    df = result["gap_df"]

    for _, row in df.iterrows():
        expected_gap = max(0, row["required_level"] - row["current_level"])
        assert row["gap"] == expected_gap
        if row["gap"] == 0:
            assert row["status"] == "Met / Strong"
        elif row["gap"] == 1:
            assert row["status"] == "Low Gap"
        else:
            assert row["status"] == "Critical Gap"


def test_charts_generation():
    employees_df = get_all_employees()
    first_id = int(employees_df.iloc[0]["id"])
    result = analyze_skill_gap(first_id)
    df = result["gap_df"]

    radar_fig = create_radar_chart(df, result["target_role"], result["employee_name"])
    assert radar_fig is not None
    assert len(radar_fig.data) == 2  # Benchmark and Employee traces

    bar_fig = create_gap_bar_chart(df)
    assert bar_fig is not None


def test_invalid_employee_id():
    with pytest.raises(ValueError):
        analyze_skill_gap(999999)
