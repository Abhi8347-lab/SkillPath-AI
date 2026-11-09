"""
Course Recommendation Engine for SkillPath AI.
Implements an explainable multi-criteria scoring algorithm and deterministic fallback
for corporate employee upskilling.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from config import (
    REC_WEIGHT_SKILL_GAP,
    REC_WEIGHT_DIFFICULTY,
    REC_WEIGHT_RATING,
    REC_WEIGHT_DURATION_FIT
)
from database import get_all_courses, get_employee_by_id
from modules.skill_gap import analyze_skill_gap


def calculate_difficulty_fit(current_level: int, course_level: int) -> float:
    """
    Evaluates learning curve alignment (0 to 100).
    Ideal scenario: course level is 1 level above current proficiency.
    """
    step = course_level - current_level
    if step == 1:
        return 100.0   # Optimal proximal development step
    elif step == 0:
        return 70.0    # Lateral consolidation
    elif step == 2:
        return 60.0    # Manageable stretch
    elif step < 0:
        return 25.0    # Too basic for current skill level
    else:
        return 20.0    # Overly advanced without prerequisites


def calculate_duration_fit(duration_hours: float, weekly_hours: float) -> float:
    """
    Evaluates feasibility of completing course within reasonable corporate pacing (2-8 weeks).
    """
    if weekly_hours <= 0:
        return 50.0
    
    estimated_weeks = duration_hours / weekly_hours
    if 2.0 <= estimated_weeks <= 6.0:
        return 100.0   # Sweet spot
    elif 1.0 <= estimated_weeks < 2.0 or 6.0 < estimated_weeks <= 8.0:
        return 80.0
    elif estimated_weeks < 1.0:
        return 70.0    # Short sprint
    else:
        return 50.0    # Protracted commitment


def recommend_courses(
    employee_id: int,
    target_role: Optional[str] = None,
    use_ai_heuristic: bool = True,
    top_n: int = 6,
    filter_skill_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generates personalized course recommendations.
    Uses AI multi-criteria heuristic weighting with deterministic fallback.
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        raise ValueError(f"Employee with ID {employee_id} not found.")

    gap_result = analyze_skill_gap(employee_id, target_role=target_role)
    gap_df = gap_result["gap_df"]
    courses_df = get_all_courses()

    if courses_df.empty:
        return []

    weekly_hours = float(emp.get("weekly_learning_hours", 5.0))

    # Map gap info by skill_id
    gap_lookup = {}
    if not gap_df.empty:
        for _, row in gap_df.iterrows():
            gap_lookup[row["skill_id"]] = {
                "skill_name": row["skill_name"],
                "current_level": int(row["current_level"]),
                "required_level": int(row["required_level"]),
                "gap": int(row["gap"]),
                "is_core": int(row["is_core"]),
                "status": row["status"]
            }

    recommendations = []

    for _, course in courses_df.iterrows():
        skill_id = course["skill_id"]
        
        # Optional user filter by specific skill
        if filter_skill_id is not None and skill_id != filter_skill_id:
            continue

        skill_info = gap_lookup.get(skill_id)
        
        if skill_info:
            current_lvl = skill_info["current_level"]
            gap_val = skill_info["gap"]
            is_core = skill_info["is_core"]
            
            # Gap relevance score
            if gap_val >= 2:
                s_gap = 100.0 if is_core else 90.0
            elif gap_val == 1:
                s_gap = 85.0 if is_core else 70.0
            else:
                s_gap = 25.0   # Skill already met
        else:
            # Skill not required for target role
            current_lvl = 0
            gap_val = 0
            is_core = 0
            s_gap = 10.0

        course_lvl = int(course["level"])
        duration = float(course["duration_hours"])
        rating = float(course["rating"])

        s_diff = calculate_difficulty_fit(current_lvl, course_lvl)
        s_rate = (rating / 5.0) * 100.0
        s_time = calculate_duration_fit(duration, weekly_hours)

        # AI Heuristic Score vs Deterministic Fallback Score
        if use_ai_heuristic:
            composite_score = (
                (REC_WEIGHT_SKILL_GAP * s_gap) +
                (REC_WEIGHT_DIFFICULTY * s_diff) +
                (REC_WEIGHT_RATING * s_rate) +
                (REC_WEIGHT_DURATION_FIT * s_time)
            )
        else:
            # Deterministic Fallback: Rule-based ranking by gap magnitude and rating
            composite_score = (gap_val * 25.0) + (is_core * 20.0) + (rating * 5.0)

        # Generate transparent explanation badge
        est_weeks = max(1, round(duration / weekly_hours, 1))
        
        reasons = []
        if gap_val > 0:
            urgency = "Critical Core Gap" if (gap_val >= 2 or is_core) else "Target Gap"
            reasons.append(f"Closes {urgency} in {course['skill_name']} (+{gap_val} levels)")
        if course_lvl == current_lvl + 1:
            reasons.append("Optimal difficulty progression (+1 level step)")
        if s_time >= 90:
            reasons.append(f"Fits your {weekly_hours}h/wk schedule (~{est_weeks} weeks)")
        if rating >= 4.8:
            reasons.append(f"Top-rated curriculum ({rating}/5.0)")

        explanation = " • ".join(reasons) if reasons else f"Recommended for {course['skill_name']} development."

        recommendations.append({
            "course_id": course["id"],
            "title": course["title"],
            "provider": course["provider"],
            "platform_url": course["platform_url"],
            "skill_id": skill_id,
            "skill_name": course["skill_name"],
            "skill_category": course["skill_category"],
            "level": course_lvl,
            "duration_hours": duration,
            "estimated_weeks": est_weeks,
            "rating": rating,
            "description": course["description"],
            "tags": course["tags"],
            "score": round(composite_score, 1),
            "gap": gap_val,
            "is_core": bool(is_core),
            "explanation": explanation
        })

    # Sort descending by recommendation score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return recommendations[:top_n]
