"""
Personalized Learning Roadmap Module.
Schedules courses into sequential phased milestones (Foundational, Core, Advanced)
based on employee weekly learning pace and renders interactive Plotly timeline/Gantt charts.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from database import get_employee_by_id
from modules.recommender import recommend_courses


def generate_learning_roadmap(
    employee_id: int,
    target_role: Optional[str] = None,
    max_courses: int = 6
) -> Dict[str, Any]:
    """
    Builds a sequential phased roadmap for an employee.
    Calculates estimated timelines, milestones, and weekly investment.
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise ValueError(f"Employee with ID {employee_id} not found.")

    weekly_hours = max(1.0, float(emp.get("weekly_learning_hours", 5.0)))
    recs = recommend_courses(employee_id, target_role=target_role, top_n=max_courses)

    if not recs:
        return {
            "employee_id": employee_id,
            "employee_name": emp["name"],
            "target_role": target_role or emp["target_role"],
            "weekly_hours": weekly_hours,
            "total_courses": 0,
            "total_hours": 0.0,
            "total_weeks": 0.0,
            "phases": {},
            "milestones": []
        }

    # Sort courses into progressive phases:
    # Level 1-2 -> Foundation, Level 3 -> Core Mastery, Level 4-5 -> Advanced & Capstone
    # Secondary sort by gap magnitude DESC
    sorted_courses = sorted(
        recs,
        key=lambda x: (x["level"], -x["gap"])
    )

    milestones = []
    current_week_start = 1.0
    total_hours = 0.0

    today = datetime.now()

    for idx, course in enumerate(sorted_courses, 1):
        duration = float(course["duration_hours"])
        course_weeks = max(1.0, round(duration / weekly_hours, 1))
        week_end = current_week_start + course_weeks
        total_hours += duration

        # Determine phase
        lvl = course["level"]
        if lvl <= 2:
            phase_num = 1
            phase_name = "Phase 1: Foundational Bridging"
            phase_color = "#10B981"  # Emerald
        elif lvl == 3:
            phase_num = 2
            phase_name = "Phase 2: Core Competency Mastery"
            phase_color = "#3B82F6"  # Blue
        else:
            phase_num = 3
            phase_name = "Phase 3: Advanced & Capstone"
            phase_color = "#8B5CF6"  # Violet

        # Approximate calendar dates
        start_date = today + timedelta(weeks=current_week_start - 1)
        end_date = today + timedelta(weeks=week_end - 1)

        milestones.append({
            "step": idx,
            "course_id": course["course_id"],
            "title": course["title"],
            "provider": course["provider"],
            "platform_url": course["platform_url"],
            "skill_name": course["skill_name"],
            "level": lvl,
            "duration_hours": duration,
            "phase_num": phase_num,
            "phase_name": phase_name,
            "phase_color": phase_color,
            "start_week": current_week_start,
            "end_week": week_end,
            "weeks_duration": course_weeks,
            "start_date": start_date.strftime("%b %d, %Y"),
            "end_date": end_date.strftime("%b %d, %Y"),
            "explanation": course["explanation"]
        })

        current_week_start = week_end

    total_weeks = round(total_hours / weekly_hours, 1)

    # Group milestones by phase
    phases = {}
    for m in milestones:
        p_name = m["phase_name"]
        if p_name not in phases:
            phases[p_name] = []
        phases[p_name].append(m)

    return {
        "employee_id": employee_id,
        "employee_name": emp["name"],
        "target_role": target_role or emp["target_role"],
        "weekly_hours": weekly_hours,
        "total_courses": len(milestones),
        "total_hours": round(total_hours, 1),
        "total_weeks": total_weeks,
        "phases": phases,
        "milestones": milestones
    }


def create_roadmap_timeline_chart(roadmap: Dict[str, Any]) -> go.Figure:
    """
    Renders an interactive Gantt-style horizontal milestone timeline
    displaying study phases, course steps, and week progression.
    """
    milestones = roadmap.get("milestones", [])
    if not milestones:
        fig = go.Figure()
        fig.update_layout(title="No milestones to display.")
        return fig

    # Build dataframe for Plotly
    df = pd.DataFrame(milestones)
    df["task_label"] = df["title"] + " (" + df["skill_name"] + ")"

    fig = go.Figure()

    # Add bar traces for each milestone
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            name=row["phase_name"],
            y=[row["task_label"]],
            x=[row["weeks_duration"]],
            base=[row["start_week"] - 1],
            orientation='h',
            marker=dict(color=row["phase_color"]),
            text=f"Wk {row['start_week']:.0f} - {row['end_week']:.0f} ({row['duration_hours']}h)",
            textposition="inside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Phase: " + row["phase_name"] + "<br>"
                "Timeline: Week " + str(row["start_week"]) + " to " + str(row["end_week"]) + "<br>"
                "Duration: " + str(row["duration_hours"]) + " study hours<br>"
                "Target Dates: " + row["start_date"] + " - " + row["end_date"] + "<br>"
                "<extra></extra>"
            ),
            showlegend=False
        ))

    fig.update_layout(
        title=f"Learning Roadmap Timeline for {roadmap['employee_name']} ({roadmap['weekly_hours']}h / week)",
        xaxis=dict(
            title="Study Progression (Weeks)",
            dtick=2,
            gridcolor="rgba(150, 150, 150, 0.2)"
        ),
        yaxis=dict(
            title="",
            autorange="reversed"  # First course at top
        ),
        height=max(350, len(milestones) * 55 + 120),
        margin=dict(l=20, r=20, t=50, b=40)
    )
    return fig
