"""
Unit tests for HR Workforce Analytics module.
"""
import pytest
from database import init_db
from modules.analytics import (
    get_workforce_overview,
    create_department_readiness_chart,
    create_org_gaps_chart,
    create_talent_mobility_donut,
    create_skill_distribution_heatmap
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_db(force_reseed=True)


def test_get_workforce_overview():
    overview = get_workforce_overview()
    assert overview["total_employees"] >= 10
    assert 0 <= overview["avg_readiness"] <= 100
    assert not overview["department_metrics"].empty
    assert not overview["employee_readiness_df"].empty
    assert not overview["top_org_gaps"].empty
    assert overview["total_enrollments"] >= 0


def test_analytics_charts():
    overview = get_workforce_overview()
    
    # Dept readiness chart
    fig_dept = create_department_readiness_chart(overview["department_metrics"])
    assert fig_dept is not None

    # Org gaps chart
    fig_gaps = create_org_gaps_chart(overview["top_org_gaps"])
    assert fig_gaps is not None

    # Mobility donut
    fig_donut = create_talent_mobility_donut(overview["employee_readiness_df"])
    assert fig_donut is not None

    # Skill heatmap
    fig_heatmap = create_skill_distribution_heatmap()
    assert fig_heatmap is not None
