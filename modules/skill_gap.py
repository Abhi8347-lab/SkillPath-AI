"""
Skill Gap Analyzer Module.
Compares employee current competencies against target role benchmarks,
computes readiness score, identifies critical skill deficits, and renders Plotly visuals.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from database import get_employee_skills, get_role_requirements, get_employee_by_id


def analyze_skill_gap(employee_id: int, target_role: str = None) -> Dict[str, Any]:
    """
    Performs comprehensive gap analysis between employee skills and target role requirements.
    If target_role is omitted, employee's designated target_role is used.
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise ValueError(f"Employee with ID {employee_id} does not exist.")

    role_to_analyze = target_role or emp["target_role"]
    role_reqs = get_role_requirements(role_to_analyze)
    
    if role_reqs.empty:
        return {
            "employee_id": employee_id,
            "employee_name": emp["name"],
            "target_role": role_to_analyze,
            "readiness_score": 0.0,
            "gap_df": pd.DataFrame(),
            "critical_gaps": [],
            "moderate_gaps": [],
            "strengths": [],
            "total_skills_required": 0
        }

    emp_skills = get_employee_skills(employee_id)
    
    # Merge role requirements with employee's current skill levels
    merged = pd.merge(
        role_reqs,
        emp_skills[["skill_id", "proficiency_level"]],
        on="skill_id",
        how="left"
    )
    merged["proficiency_level"] = merged["proficiency_level"].fillna(0).astype(int)
    merged = merged.rename(columns={"proficiency_level": "current_level"})
    
    # Calculate gap metrics
    # gap = max(0, required_level - current_level)
    merged["gap"] = (merged["required_level"] - merged["current_level"]).clip(lower=0)
    
    def categorize_gap(row):
        if row["gap"] == 0:
            return "Met / Strong"
        elif row["gap"] == 1:
            return "Low Gap"
        else:
            return "Critical Gap"

    merged["status"] = merged.apply(categorize_gap, axis=1)

    # Weighted Readiness Score:
    # Core skills have weight 1.5, non-core have weight 1.0
    merged["weight"] = merged["is_core"].apply(lambda c: 1.5 if c == 1 else 1.0)
    merged["achieved_weighted"] = np.minimum(merged["current_level"], merged["required_level"]) * merged["weight"]
    merged["target_weighted"] = merged["required_level"] * merged["weight"]

    total_achieved = merged["achieved_weighted"].sum()
    total_target = merged["target_weighted"].sum()

    readiness_score = round((total_achieved / total_target * 100), 1) if total_target > 0 else 0.0

    critical_gaps = merged[(merged["gap"] >= 2) | ((merged["gap"] >= 1) & (merged["is_core"] == 1))].to_dict(orient="records")
    moderate_gaps = merged[(merged["gap"] == 1) & (merged["is_core"] == 0)].to_dict(orient="records")
    strengths = merged[merged["gap"] == 0].to_dict(orient="records")

    return {
        "employee_id": employee_id,
        "employee_name": emp["name"],
        "target_role": role_to_analyze,
        "readiness_score": readiness_score,
        "gap_df": merged,
        "critical_gaps": critical_gaps,
        "moderate_gaps": moderate_gaps,
        "strengths": strengths,
        "total_skills_required": len(merged)
    }


def create_radar_chart(gap_df: pd.DataFrame, role_name: str, employee_name: str) -> go.Figure:
    """
    Builds an interactive Plotly Radar (Spider) chart comparing
    current employee proficiency against benchmark requirements.
    """
    if gap_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No role benchmark requirements found.")
        return fig

    skills = gap_df["skill_name"].tolist()
    required = gap_df["required_level"].tolist()
    current = gap_df["current_level"].tolist()

    # Close the loop for radar chart
    skills_closed = skills + [skills[0]]
    required_closed = required + [required[0]]
    current_closed = current + [current[0]]

    fig = go.Figure()

    # Target Benchmark Trace
    fig.add_trace(go.Scatterpolar(
        r=required_closed,
        theta=skills_closed,
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.15)',
        line=dict(color='#6366F1', width=2, dash='dot'),
        name=f"Benchmark: {role_name}"
    ))

    # Current Employee Trace
    fig.add_trace(go.Scatterpolar(
        r=current_closed,
        theta=skills_closed,
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.25)',
        line=dict(color='#10B981', width=3),
        name=f"Current: {employee_name}"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["1: Novice", "2: Elem", "3: Inter", "4: Adv", "5: Expert"],
                gridcolor="rgba(150, 150, 150, 0.2)"
            ),
            angularaxis=dict(
                gridcolor="rgba(150, 150, 150, 0.2)"
            )
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=40, b=40),
        height=450
    )
    return fig


def create_gap_bar_chart(gap_df: pd.DataFrame) -> go.Figure:
    """
    Creates an interactive horizontal bar chart showcasing skill gap magnitudes
    color-coded by severity (Met, Low Gap, Critical Gap).
    """
    if gap_df.empty:
        return go.Figure()

    df_sorted = gap_df.sort_values(by="gap", ascending=True).copy()
    
    color_map = {
        "Met / Strong": "#10B981",    # Emerald Green
        "Low Gap": "#F59E0B",         # Amber
        "Critical Gap": "#EF4444"     # Rose / Red
    }

    df_sorted["color"] = df_sorted["status"].map(color_map)

    fig = go.Figure()

    for status_label in ["Met / Strong", "Low Gap", "Critical Gap"]:
        sub = df_sorted[df_sorted["status"] == status_label]
        if not sub.empty:
            fig.add_trace(go.Bar(
                y=sub["skill_name"],
                x=sub["gap"],
                orientation='h',
                name=status_label,
                marker=dict(color=color_map[status_label]),
                text=[f"Gap: {g} (Req: {r}, Curr: {c})" for g, r, c in zip(sub["gap"], sub["required_level"], sub["current_level"])],
                textposition="auto"
            ))

    fig.update_layout(
        title="Skill Gap Severity Breakdown",
        xaxis=dict(title="Skill Gap (Levels to Target)", range=[0, 5], dtick=1),
        yaxis=dict(title="Skills"),
        barmode='stack',
        height=400,
        margin=dict(l=20, r=20, t=50, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    return fig
