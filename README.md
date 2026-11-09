# 🎯 SkillPath AI – Corporate Upskilling & Talent Intelligence Platform

> **AI-Powered, Deterministic, and Explainable Employee Upskilling Platform**  
> Built for corporate HR leaders, engineering managers, and ambitious employees to close critical organizational skill gaps.

---

## 🌟 Key Highlights for Hackathon Judges

1. **Deterministic AI & Zero External LLM Dependency**:
   - Uses a multi-criteria proximal development algorithm combining **Skill Gap Relevance (45%)**, **Difficulty Alignment (25%)**, **Course Rating Quality (15%)**, and **Time Commitment Fit (15%)**.
   - Built-in **Deterministic Fallback Engine** guarantees zero hallucinations and full operability without external API keys or network latency.
2. **Explainable AI Recommendations**:
   - Every course recommendation provides a transparent explanation badge (e.g., *"Closes Critical Core Gap in Machine Learning (+2 levels), fits your 6h/wk schedule (~5.8 wks), rated 4.9/5"*).
3. **Verified Real-World Course Catalog**:
   - Contains authentic links to top industry courses from **Harvard CS50, MIT OpenCourseWare, DeepLearning.AI, freeCodeCamp, AWS, Google Cloud, and GitHub Skills**. No invented URLs.
4. **Objective Diagnostic Mini-Quiz**:
   - Mitigates self-assessment bias through standardized domain questions that suggest an objective proficiency baseline.
5. **Interactive Data Visualizations (Plotly)**:
   - Polar/Spider Competency Radar charts comparing employee proficiency against target role benchmarks.
   - Skill Gap Severity breakdowns (Met, Low Gap, Critical Gap).
   - Dynamic Gantt-style Learning Roadmap with sequential phased milestones.
   - Company-wide Departmental Readiness, Talent Mobility distribution, and Skill Proficiency Heatmap.
6. **Closed-Loop Learning Progress Tracker**:
   - Course completion dynamically elevates the employee's skill rating in the database, recomputes their role readiness score, and awards gamified achievement badges.

---

## 🛠️ Technology Stack

- **Python 3.11+ / 3.13**
- **Streamlit** (Interactive enterprise web application)
- **Pandas & NumPy** (Vectorized skill matrices, gap analytics, and multi-criteria scoring)
- **Plotly** (Interactive radar charts, timeline Gantt charts, heatmaps, and analytics)
- **SQLite** (Relational persistence with foreign keys, seed data, and transaction safety)
- **Pytest** (Automated unit and end-to-end integration test suite)

---

## 📁 Project Architecture

```
AAROHAN/
├── app.py                      # Streamlit application entrypoint & UI layout
├── config.py                   # Domain constants, role definitions, scoring weights
├── database.py                 # SQLite schema, query helpers, and enterprise seed data
├── modules/
│   ├── __init__.py
│   ├── assessment.py           # Employee validation, profile CRUD, diagnostic quiz
│   ├── skill_gap.py            # Gap calculation, readiness score, radar & bar charts
│   ├── recommender.py          # AI multi-criteria scoring, deterministic fallback
│   ├── roadmap.py              # Phased learning trajectory, timeline Gantt chart
│   ├── tracker.py              # Enrollments, progress logging, auto-skill promotion
│   └── analytics.py            # HR workforce intelligence, heatmaps, talent mobility
├── tests/
│   ├── test_database.py        # Database schema and seed data tests
│   ├── test_assessment.py      # Input validation and quiz scoring tests
│   ├── test_skill_gap.py       # Gap formulas, weights, and chart tests
│   ├── test_recommender.py     # Heuristic ranking and fallback tests
│   ├── test_roadmap.py         # Sequential pacing and phase tests
│   ├── test_tracker.py         # Progress updates and auto-level-up tests
│   ├── test_analytics.py       # Workforce metrics and heatmap tests
│   └── test_integration.py    # End-to-end employee upskilling lifecycle test
├── data/
│   └── skillpath.db            # SQLite database file
├── pytest.ini                  # Pytest configuration
├── PROJECT_RULES.md            # Hackathon development rules & standards
└── README.md                   # Documentation and project overview
```

---

## 🚀 Getting Started

### 1. Running the Streamlit Web Application
Activate your Python environment and run:

```bash
streamlit run app.py
```
Or directly using the virtual environment:
```bash
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

### 2. Running Automated Tests
Run all 30 unit and integration tests:

```bash
.\.venv\Scripts\python.exe -m pytest --ignore=.venv -v
```

---

## 🧭 Application Modules & Workflow

### 1. Executive Dashboard
- Active employee profile switcher in sidebar (pre-seeded with 10 diverse roles).
- Quick KPI metrics: Target Role Readiness %, Critical Gaps count, Active Enrollments, and Total Study Hours.
- Competency Radar chart and one-click quick enrollment.

### 2. Skill Assessment
- **Profile Management**: Input validation for employee name, email, department, current and target role, experience, and weekly hours.
- **Self-Assessment Sliders**: 1 to 5 scale (*Beginner, Elementary, Intermediate, Advanced, Expert*) across 6 skill categories.
- **Diagnostic Mini-Quiz**: Standardized multiple-choice questions calculating an objective proficiency baseline.

### 3. Skill Gap Analyzer
- Calculates weighted readiness score giving higher importance (1.5x) to core competencies.
- Color-coded severity: Met/Strong (Green), Low Gap (Amber), Critical Gap (Red).
- Interactive Radar/Spider chart and Gap Magnitude chart.
- Supports **What-If simulation** by changing the target role dropdown.

### 4. Course Recommendation Engine
- Multi-criteria heuristic scoring combining gap relevance, optimal difficulty progression (+1 level step), verified rating, and weekly hour feasibility.
- Toggle for **Deterministic Fallback mode**.
- Filter by specific skill.
- Transparent "Why Recommended" explainability badge on every card with direct links to verified courses.

### 5. Personalized Learning Roadmap
- Sequential phased milestones:
  - **Phase 1: Foundational Bridging** (Weeks 1-4)
  - **Phase 2: Core Competency Mastery** (Weeks 5-10)
  - **Phase 3: Advanced & Capstone** (Weeks 11+)
- Interactive Gantt chart calculating milestone schedules and target calendar dates.

### 6. Learning Progress Tracker
- Interactive progress slider (0% to 100%).
- **Auto-Promotion Engine**: When a course hits 100%, the employee's skill level is automatically boosted in the database with celebratory feedback!
- Study activity logger recording hours and notes.
- Gamified achievement badges (Initiative, Dedicated Learner, Course Finisher, Skill Champion, Versatile Talent).

### 7. HR Workforce Analytics
- Macro-level talent intelligence for executives and HR leaders.
- Departmental Skill Readiness Index (%) with benchmark target line.
- Talent Mobility Distribution donut chart (Ready for Transition vs Upskilling in Progress vs Early Growth).
- Company-wide Top Organizational Skill Gaps bar chart.
- Departmental Skill Proficiency Heatmap.

---

## 🔒 Security & Data Integrity
- Strict regex and numeric range validation for all user inputs.
- SQLite foreign key constraints and transaction safety.
- Zero hardcoded credentials or API keys.
- Completely self-contained and reproducible.
