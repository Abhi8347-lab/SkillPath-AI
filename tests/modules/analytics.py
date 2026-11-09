"""
HR Workforce Analytics Module.
Provides macro-level talent intelligence, department readiness benchmarks,
company-wide skill gap heatmaps, and upskilling ROI dashboards.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from database import (
    get_db_connection,
    get_all_employees,
    get_all_skills
)
from modules.skill_gap import analyze_skill_gap


def get_workforce_overview() -> Dict[str, Any]:
    """
    Computes company-wide talent analytics, employee readiness distribution,
    department summaries, and organizational skill gaps.
    """
    employees_df = get_all_employees()
    if employees_df.empty:
        return {
            "total_employees": 0,
            "avg_readiness": 0.0,
            "department_metrics": pd.DataFrame(),
            "employee_readiness_df": pd.DataFrame(),
            "top_org_gaps": pd.DataFrame(),
            "overall_training_hours": 0.0,
            "total_enrollments": 0
        }

    readiness_records = []
    all_gaps = []

    for _, emp in employees_df.iterrows():
        emp_id = int(emp["id"])
        gap_res = analyze_skill_gap(emp_id)
        r_score = gap_res["readiness_score"]
        
        # Determine talent mobility status
        if r_score >= 80.0:
            mobility = "Ready for Transition"
        elif r_score >= 55.0:
            mobility = "Upskilling In Progress"
        else:
            mobility = "Early Growth Stage"

        readiness_records.append({
            "employee_id": emp_id,
            "name": emp["name"],
            "department": emp["department"],
            "current_role": emp["current_role"],
            "target_role": emp["target_role"],
            "readiness_score": r_score,
            "mobility_status": mobility,
            "critical_gap_count": len(gap_res["critical_gaps"])
        })

        # Collect individual gaps for org-level aggregation
        gap_df = gap_res["gap_df"]
        if not gap_df.empty:
            for _, g_row in gap_df.iterrows():
                if g_row["gap"] > 0:
                    all_gaps.append({
                        "skill_id": g_row["skill_id"],
                        "skill_name": g_row["skill_name"],
                        "category": g_row["category"],
                        "gap": g_row["gap"],
                        "is_core": g_row["is_core"],
                        "department": emp["department"]
                    })

    emp_readiness_df = pd.DataFrame(readiness_records)
    avg_readiness = round(float(emp_readiness_df["readiness_score"].mean()), 1)

    # Department level aggregation
    dept_metrics = emp_readiness_df.groupby("department").agg(
        employee_count=("employee_id", "count"),
        avg_readiness=("readiness_score", "mean"),
        ready_for_transition=("mobility_status", lambda x: (x == "Ready for Transition").sum())
    ).reset_index()
    dept_metrics["avg_readiness"] = dept_metrics["avg_readiness"].round(1)

    # Company-wide top skill gaps
    if all_gaps:
        gaps_df = pd.DataFrame(all_gaps)
        top_org_gaps = gaps_df.groupby(["skill_name", "category"]).agg(
            employees_affected=("gap", "count"),
            avg_gap_magnitude=("gap", "mean"),
            core_gap_count=("is_core", "sum")
        ).reset_index().sort_values(by="employees_affected", ascending=False)
        top_org_gaps["avg_gap_magnitude"] = top_org_gaps["avg_gap_magnitude"].round(1)
    else:
        top_org_gaps = pd.DataFrame(columns=["skill_name", "category", "employees_affected", "avg_gap_magnitude", "core_gap_count"])

    # Training hours from database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(hours_spent), 0.0) FROM learning_logs")
        total_hours = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(id) FROM enrollments")
        total_enrollments = cursor.fetchone()[0]

    return {
        "total_employees": len(employees_df),
        "avg_readiness": avg_readiness,
        "department_metrics": dept_metrics,
        "employee_readiness_df": emp_readiness_df,
        "top_org_gaps": top_org_gaps,
        "overall_training_hours": round(float(total_hours), 1),
        "total_enrollments": total_enrollments
    }


def create_department_readiness_chart(dept_metrics: pd.DataFrame) -> go.Figure:
    """
    Renders bar chart of average skill readiness index across corporate departments.
    """
    if dept_metrics.empty:
        return go.Figure()

    fig = px.bar(
        dept_metrics,
        x="department",
        y="avg_readiness",
        color="avg_readiness",
        color_continuous_scale="Viridis",
        text="avg_readiness",
        title="Departmental Upskilling Readiness Index (%)",
        labels={"avg_readiness": "Avg Readiness (%)", "department": "Department"}
    )
    fig.add_hline(y=75, line_dash="dash", line_color="#EF4444", annotation_text="Target Benchmark (75%)")
    fig.update_layout(yaxis=dict(range=[0, 100]), height=400, margin=dict(l=20, r=20, t=50, b=30))
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    return fig


def create_org_gaps_chart(top_org_gaps: pd.DataFrame, top_n: int = 8) -> go.Figure:
    """
    Renders horizontal bar chart of top skills with widest gaps across company.
    """
    if top_org_gaps.empty:
        return go.Figure()

    df_subset = top_org_gaps.head(top_n).sort_values(by="employees_affected", ascending=True)

    fig = px.bar(
        df_subset,
        y="skill_name",
        x="employees_affected",
        orientation='h',
        color="avg_gap_magnitude",
        color_continuous_scale="Reds",
        title=f"Top {top_n} Organizational Skill Gaps (Employees Impacted)",
        labels={"employees_affected": "Number of Employees Deficient", "skill_name": "Skill", "avg_gap_magnitude": "Avg Gap (Levels)"}
    )
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=30))
    return fig


def create_talent_mobility_donut(emp_readiness_df: pd.DataFrame) -> go.Figure:
    """
    Renders a donut chart illustrating employee talent mobility readiness proportions.
    """
    if emp_readiness_df.empty:
        return go.Figure()

    counts = emp_readiness_df["mobility_status"].value_counts().reset_index()
    counts.columns = ["status", "count"]

    color_discrete_map = {
        "Ready for Transition": "#10B981",    # Emerald
        "Upskilling In Progress": "#3B82F6",  # Blue
        "Early Growth Stage": "#F59E0B"      # Amber
    }

    fig = px.pie(
        counts,
        names="status",
        values="count",
        hole=0.45,
        title="Workforce Talent Mobility Distribution",
        color="status",
        color_discrete_map=color_discrete_map
    )
    fig.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=30))
    return fig


def create_skill_distribution_heatmap() -> go.Figure:
    """
    Generates a company-wide skill proficiency heatmap across departments and skills.
    """
    with get_db_connection() as conn:
        query = """
            SELECT e.department, s.name AS skill_name, AVG(es.proficiency_level) AS avg_level
            FROM employee_skills es
            JOIN employees e ON es.employee_id = e.id
            JOIN skills s ON es.skill_id = s.id
            GROUP BY e.department, s.name
        """
        df = pd.read_sql_query(query, conn)

    if df.empty:
        return go.Figure()

    pivot = df.pivot(index="skill_name", columns="department", values="avg_level").fillna(0).round(1)

    fig = px.imshow(
        pivot,
        labels=dict(x="Department", y="Skill", color="Proficiency (1-5)"),
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        color_continuous_scale="Blues",
        aspect="auto",
        title="Departmental Skill Proficiency Heatmap (Avg Level 1-5)"
    )
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=50, b=30))
    return fig
