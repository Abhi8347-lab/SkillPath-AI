"""
Employee Skill Assessment Module.
Handles validation, profile creation/updates, self-assessments, and objective diagnostic quizzes.
"""
import re
from typing import Dict, Any, Tuple, Optional, List
import sqlite3
from database import get_db_connection, get_employee_by_id, get_employee_skills


EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"


def validate_employee_input(
    name: str,
    email: str,
    department: str,
    current_role: str,
    target_role: str,
    experience_years: float,
    weekly_learning_hours: float
) -> Tuple[bool, Optional[str]]:
    """
    Validates employee registration / update inputs.
    Returns (is_valid, error_message).
    """
    if not name or not name.strip():
        return False, "Employee full name cannot be blank."
    
    if len(name.strip()) < 2:
        return False, "Employee name must be at least 2 characters."
        
    if not email or not re.match(EMAIL_REGEX, email.strip()):
        return False, "Please enter a valid corporate email address (e.g. employee@company.com)."
        
    if not department or not department.strip():
        return False, "Department selection is required."
        
    if not current_role or not current_role.strip():
        return False, "Current role designation is required."
        
    if not target_role or not target_role.strip():
        return False, "Target aspirational role is required."
        
    try:
        exp = float(experience_years)
        if exp < 0.0 or exp > 50.0:
            return False, "Experience years must be between 0.0 and 50.0."
    except (ValueError, TypeError):
        return False, "Experience years must be a valid number."
        
    try:
        hrs = float(weekly_learning_hours)
        if hrs < 1.0 or hrs > 40.0:
            return False, "Weekly learning hours must be between 1.0 and 40.0 hours."
    except (ValueError, TypeError):
        return False, "Weekly learning hours must be a valid number."
        
    return True, None


def validate_proficiency_level(level: int) -> bool:
    """Validates that a proficiency score is between 1 (Novice) and 5 (Expert)."""
    return isinstance(level, int) and 1 <= level <= 5


def save_or_update_employee(
    name: str,
    email: str,
    department: str,
    current_role: str,
    target_role: str,
    experience_years: float,
    weekly_learning_hours: float,
    employee_id: Optional[int] = None
) -> Tuple[Optional[int], Optional[str]]:
    """
    Creates a new employee or updates an existing employee profile after validation.
    Returns (employee_id, error_message).
    """
    is_valid, error = validate_employee_input(
        name, email, department, current_role, target_role, experience_years, weekly_learning_hours
    )
    if not is_valid:
        return None, error

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if employee_id:
            # Update existing
            cursor.execute("""
                UPDATE employees
                SET name = ?, email = ?, department = ?, current_role = ?, 
                    target_role = ?, experience_years = ?, weekly_learning_hours = ?
                WHERE id = ?
            """, (name.strip(), email.strip().lower(), department.strip(), 
                  current_role.strip(), target_role.strip(), float(experience_years), 
                  float(weekly_learning_hours), employee_id))
            conn.commit()
            return employee_id, None
        else:
            # Check unique email
            cursor.execute("SELECT id FROM employees WHERE LOWER(email) = ?", (email.strip().lower(),))
            existing = cursor.fetchone()
            if existing:
                return None, f"An employee with email '{email}' already exists."

            cursor.execute("""
                INSERT INTO employees (name, email, department, current_role, target_role, experience_years, weekly_learning_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name.strip(), email.strip().lower(), department.strip(), 
                  current_role.strip(), target_role.strip(), float(experience_years), 
                  float(weekly_learning_hours)))
            conn.commit()
            return cursor.lastrowid, None


def save_employee_skill_assessment(employee_id: int, skill_ratings: Dict[int, int]) -> Tuple[bool, Optional[str]]:
    """
    Saves or updates proficiency ratings (1-5) for an employee across specified skills.
    Returns (success, error_message).
    """
    emp = get_employee_by_id(employee_id)
    if not emp:
        return False, f"Employee with ID {employee_id} not found."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for skill_id, level in skill_ratings.items():
            if not validate_proficiency_level(level):
                return False, f"Proficiency level for skill ID {skill_id} must be an integer between 1 and 5."
            
            cursor.execute("""
                INSERT INTO employee_skills (employee_id, skill_id, proficiency_level, last_assessed)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(employee_id, skill_id) DO UPDATE SET
                    proficiency_level = excluded.proficiency_level,
                    last_assessed = CURRENT_TIMESTAMP
            """, (employee_id, skill_id, level))
        
        conn.commit()
    return True, None


# --- Objective Diagnostic Mini-Quiz System ---

DIAGNOSTIC_QUESTIONS = [
    {
        "id": 1,
        "category": "Programming & Software",
        "skill": "Python Programming",
        "question": "Which Python built-in function or syntax is best suited for lazily generating an infinite sequence without storing all elements in memory?",
        "options": [
            "List comprehension with range()",
            "Generator function using the 'yield' keyword",
            "Tuple conversion using tuple()",
            "Recursive function calls"
        ],
        "answer_idx": 1,
        "difficulty": 3
    },
    {
        "id": 2,
        "category": "Data Science & AI",
        "skill": "SQL & Relational Databases",
        "question": "What is the primary difference between WHERE and HAVING clauses in SQL?",
        "options": [
            "HAVING filters individual rows before grouping, WHERE filters aggregated results after grouping",
            "WHERE filters rows prior to aggregation, HAVING filters aggregate grouped values",
            "WHERE only works with integers, HAVING works with strings",
            "There is no difference; they are interchangeable"
        ],
        "answer_idx": 1,
        "difficulty": 2
    },
    {
        "id": 3,
        "category": "Data Science & AI",
        "skill": "Machine Learning",
        "question": "When a machine learning model achieves near 100% training accuracy but performs poorly on unseen test data, what is this called and how is it mitigated?",
        "options": [
            "Underfitting; add more polynomial features",
            "Overfitting; apply regularization, dropout, or collect more data",
            "Vanishing gradients; increase learning rate",
            "Data leakage; eliminate test data"
        ],
        "answer_idx": 1,
        "difficulty": 3
    },
    {
        "id": 4,
        "category": "Cloud & DevOps",
        "skill": "Docker & Containerization",
        "question": "What is the key benefit of multi-stage Docker builds?",
        "options": [
            "They allow running multiple containers on the same port",
            "They drastically reduce final production image size by separating build tools from runtime artifacts",
            "They eliminate the need for Dockerfiles",
            "They encrypt container filesystems automatically"
        ],
        "answer_idx": 1,
        "difficulty": 3
    },
    {
        "id": 5,
        "category": "Cloud & DevOps",
        "skill": "Kubernetes",
        "question": "In Kubernetes, which resource ensures a specified number of identical Pod replicas are running at any given time?",
        "options": [
            "ReplicaSet / Deployment",
            "ConfigMap",
            "Ingress Controller",
            "PersistentVolumeClaim"
        ],
        "answer_idx": 0,
        "difficulty": 3
    },
    {
        "id": 6,
        "category": "Cybersecurity",
        "skill": "Cybersecurity Fundamentals",
        "question": "According to the principle of least privilege (PoLP), how should permissions be granted to users and applications?",
        "options": [
            "Grant root/admin access by default to avoid permission friction",
            "Grant only the minimum necessary access rights required to perform designated tasks",
            "Allow unrestricted read access while restricting write access",
            "Grant temporary 24-hour admin tokens for every login"
        ],
        "answer_idx": 1,
        "difficulty": 2
    }
]


def score_diagnostic_quiz(user_answers: Dict[int, int]) -> Dict[str, Any]:
    """
    Scores diagnostic quiz answers and suggests skill proficiency baselines.
    user_answers: {question_id: selected_option_index}
    """
    total = len(DIAGNOSTIC_QUESTIONS)
    correct = 0
    breakdown = []

    for q in DIAGNOSTIC_QUESTIONS:
        qid = q["id"]
        selected = user_answers.get(qid)
        is_correct = (selected == q["answer_idx"])
        if is_correct:
            correct += 1
        breakdown.append({
            "question_id": qid,
            "skill": q["skill"],
            "category": q["category"],
            "is_correct": is_correct,
            "selected_option": q["options"][selected] if selected is not None and 0 <= selected < len(q["options"]) else "Skipped",
            "correct_option": q["options"][q["answer_idx"]]
        })

    score_pct = round((correct / total) * 100, 1) if total > 0 else 0.0
    
    # Suggested baseline proficiency based on quiz performance
    if score_pct >= 85:
        suggested_baseline = 4  # Advanced
    elif score_pct >= 65:
        suggested_baseline = 3  # Intermediate
    elif score_pct >= 40:
        suggested_baseline = 2  # Elementary
    else:
        suggested_baseline = 1  # Beginner

    return {
        "total_questions": total,
        "correct_answers": correct,
        "score_pct": score_pct,
        "suggested_baseline": suggested_baseline,
        "breakdown": breakdown
    }
