"""
Configuration constants and domain settings for SkillPath AI.
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "skillpath.db"

# Proficiency Level Scale (1 to 5)
PROFICIENCY_LEVELS = {
    1: {"name": "Beginner / Novice", "desc": "Basic conceptual understanding, needs guidance."},
    2: {"name": "Elementary", "desc": "Can perform routine tasks with supervision."},
    3: {"name": "Intermediate", "desc": "Independent practitioner, solves standard problems."},
    4: {"name": "Advanced", "desc": "Deep working knowledge, guides others and designs solutions."},
    5: {"name": "Expert", "desc": "Authoritative subject matter expert, innovates and architects."}
}

# Skill Categories
SKILL_CATEGORIES = [
    "Programming & Software",
    "Data Science & AI",
    "Cloud & DevOps",
    "Cybersecurity",
    "Product & Agile Leadership",
    "Core Engineering"
]

# Standard Target Roles
STANDARD_ROLES = [
    "AI / ML Engineer",
    "Data Scientist",
    "Cloud & DevOps Architect",
    "Senior Full Stack Developer",
    "Cybersecurity Analyst",
    "Product Manager (Tech)",
    "Data Analyst",
    "Site Reliability Engineer (SRE)"
]

# Corporate Departments
DEPARTMENTS = [
    "Engineering",
    "Data & Analytics",
    "Cloud & Infrastructure",
    "Cybersecurity",
    "Product & Design"
]

# Recommendation Weights (Transparent AI Heuristic)
REC_WEIGHT_SKILL_GAP = 0.45      # Priority given to critical gap reduction
REC_WEIGHT_DIFFICULTY = 0.25     # Alignment with employee's current level
REC_WEIGHT_RATING = 0.15         # Verified course quality/rating
REC_WEIGHT_DURATION_FIT = 0.15   # Feasibility based on weekly learning hours
