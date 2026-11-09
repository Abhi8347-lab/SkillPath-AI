# SkillPath AI – Development Rules & Architecture Guidelines

## Project Objective
SkillPath AI is an AI-powered corporate employee upskilling recommendation platform built for hackathon demonstration and corporate deployment.

## Technology Stack
- **Python 3.11+**
- **Streamlit** (Interactive Frontend & Dashboards)
- **Pandas & NumPy** (Data processing, skill matrix, scoring algorithms)
- **Plotly** (Interactive radar charts, roadmaps, heatmaps, workforce analytics)
- **SQLite** (Persistent, lightweight relational database with zero external config)

## Development Rules
1. **Clean, Modular Code**: Separation of concerns between UI (`app.py`), DB (`database.py`), and domain logic (`modules/`).
2. **Small, Understandable Functions**: Every function has a single responsibility and type hints.
3. **Meaningful Variable Names**: Avoid cryptic abbreviations; use clear names like `proficiency_level`, `skill_gap_score`.
4. **Transparent Explainable Logic**: Document AI scoring weights and gap analysis calculations.
5. **No Unnecessary Libraries**: Zero bloated dependencies; rely on standard library and core approved tools.
6. **Integrity & Review**: Never overwrite working files without diff reviews.
7. **Security**: Zero hardcoded credentials or API keys.
8. **Real Course URLs**: Only genuine, verified URLs from established platforms (Coursera, edX, MIT OCW, freeCodeCamp, official documentation).
9. **Strict Validation**: Validate emails, experience years, study hours, and proficiency ranges (1-5).
10. **Deterministic Fallback**: The recommendation system works deterministically even without external AI/LLMs.
11. **Test-Driven Reliability**: Every core module is thoroughly covered by automated unit tests with `pytest`.
