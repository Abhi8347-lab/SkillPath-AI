"""
Learning Progress Tracker Module.
Manages course enrollments, progress logging, study hours recording,
automatic skill elevation upon course completion, and achievement badges.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd

from database import (
    get_db_connection,
    get_employee_enrollments,
    get_employee_by_id,
    get_employee_skills
)


def enroll_employee_in_course(employee_id: int, course_id: int) -> Tuple[bool, Optional[str]]:
    """
    Enrolls an employee into a course if not already enrolled.
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        return False, f"Employee {employee_id} does not exist."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM enrollments WHERE employee_id = ? AND course_id = ?", (employee_id, course_id))
        existing = cursor.fetchone()
        if existing:
            return False, f"Employee is already enrolled in this course (Status: {existing['status']})."

        cursor.execute("""
            INSERT INTO enrollments (employee_id, course_id, status, progress_pct)
            VALUES (?, ?, 'in_progress', 0)
        """, (employee_id, course_id))
        conn.commit()
    return True, None


def update_course_progress(
    employee_id: int,
    course_id: int,
    progress_pct: int
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Updates enrollment completion percentage (0-100).
    When progress reaches 100%, automatically marks status as 'completed',
    stamps completion timestamp, and triggers skill elevation!
    Returns (success, error_msg, notification_msg).
    """
    if not (0 <= progress_pct <= 100):
        return False, "Progress percentage must be between 0 and 100.", None

    notification = None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.status, c.skill_id, c.level, c.title, s.name AS skill_name
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            JOIN skills s ON c.skill_id = s.id
            WHERE e.employee_id = ? AND e.course_id = ?
        """, (employee_id, course_id))
        row = cursor.fetchone()
        
        if not row:
            return False, "Enrollment record not found.", None

        previous_status = row["status"]
        skill_id = row["skill_id"]
        course_level = row["level"]
        skill_name = row["skill_name"]
        course_title = row["title"]

        if progress_pct == 100:
            new_status = "completed"
            cursor.execute("""
                UPDATE enrollments
                SET progress_pct = 100, status = 'completed', completed_date = CURRENT_TIMESTAMP
                WHERE employee_id = ? AND course_id = ?
            """, (employee_id, course_id))

            # Trigger Skill Level Up
            cursor.execute("""
                SELECT proficiency_level FROM employee_skills
                WHERE employee_id = ? AND skill_id = ?
            """, (employee_id, skill_id))
            curr_skill = cursor.fetchone()
            current_lvl = curr_skill["proficiency_level"] if curr_skill else 0

            # Level up logic: if course_level > current_lvl, elevate to course_level.
            # If current_lvl == course_level, increment by +1 (capped at 5).
            new_lvl = max(current_lvl, course_level)
            if new_lvl == current_lvl and current_lvl < 5:
                new_lvl = current_lvl + 1
            new_lvl = min(5, max(1, new_lvl))

            cursor.execute("""
                INSERT INTO employee_skills (employee_id, skill_id, proficiency_level, last_assessed)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(employee_id, skill_id) DO UPDATE SET
                    proficiency_level = excluded.proficiency_level,
                    last_assessed = CURRENT_TIMESTAMP
            """, (employee_id, skill_id, new_lvl))

            notification = f"🎉 Course '{course_title}' completed! Your proficiency in {skill_name} elevated from Level {current_lvl} to Level {new_lvl}!"
        else:
            new_status = "in_progress" if progress_pct > 0 else "not_started"
            cursor.execute("""
                UPDATE enrollments
                SET progress_pct = ?, status = ?, completed_date = NULL
                WHERE employee_id = ? AND course_id = ?
            """, (progress_pct, new_status, employee_id, course_id))

        conn.commit()

    return True, None, notification


def log_learning_activity(
    employee_id: int,
    course_id: int,
    hours_spent: float,
    notes: str = ""
) -> Tuple[bool, Optional[str]]:
    """
    Logs study session hours and optional notes for an employee.
    """
    if hours_spent <= 0:
        return False, "Hours spent must be greater than 0."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO learning_logs (employee_id, course_id, hours_spent, notes)
            VALUES (?, ?, ?, ?)
        """, (employee_id, course_id, float(hours_spent), notes.strip()))
        conn.commit()
    return True, None


def get_employee_tracker_summary(employee_id: int) -> Dict[str, Any]:
    """
    Aggregates learning metrics, logged hours, active enrollments, and unlocked achievement badges.
    """
    enrollments_df = get_employee_enrollments(employee_id)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(hours_spent), 0.0) AS total_hours, COUNT(id) AS total_sessions
            FROM learning_logs
            WHERE employee_id = ?
        """, (employee_id,))
        stats = cursor.fetchone()
        total_hours = float(stats["total_hours"]) if stats else 0.0
        total_sessions = int(stats["total_sessions"]) if stats else 0

        # Recent logs
        cursor.execute("""
            SELECT l.hours_spent, l.notes, l.logged_at, c.title AS course_title
            FROM learning_logs l
            JOIN courses c ON l.course_id = c.id
            WHERE l.employee_id = ?
            ORDER BY l.logged_at DESC LIMIT 5
        """, (employee_id,))
        recent_logs = [dict(r) for r in cursor.fetchall()]

    active_courses = 0
    completed_courses = 0
    avg_progress = 0.0

    if not enrollments_df.empty:
        completed_courses = len(enrollments_df[enrollments_df["status"] == "completed"])
        active_courses = len(enrollments_df[enrollments_df["status"] == "in_progress"])
        avg_progress = round(float(enrollments_df["progress_pct"].mean()), 1)

    # Gamified Badges calculation
    badges = []
    if len(enrollments_df) >= 1:
        badges.append({"title": "Initiative", "icon": "🚀", "desc": "Enrolled in first upskilling course"})
    if total_hours >= 5.0:
        badges.append({"title": "Dedicated Learner", "icon": "⏱️", "desc": "Logged over 5 hours of study time"})
    if completed_courses >= 1:
        badges.append({"title": "Course Finisher", "icon": "🎓", "desc": "Successfully completed a course"})
    if completed_courses >= 3:
        badges.append({"title": "Skill Champion", "icon": "🏆", "desc": "Completed 3+ upskilling courses"})
    if not enrollments_df.empty and len(enrollments_df["skill_name"].unique()) >= 2:
        badges.append({"title": "Versatile Talent", "icon": "🌟", "desc": "Learning cross-domain competencies"})

    return {
        "employee_id": employee_id,
        "enrollments_df": enrollments_df,
        "total_enrollments": len(enrollments_df),
        "active_courses": active_courses,
        "completed_courses": completed_courses,
        "avg_progress": avg_progress,
        "total_hours": round(total_hours, 1),
        "total_sessions": total_sessions,
        "recent_logs": recent_logs,
        "badges": badges
    }
