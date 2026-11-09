"""
SkillPath AI – AI-Powered Corporate Employee Upskilling Platform
Main Streamlit Application
"""
import streamlit as st
import pandas as pd
import numpy as np

from config import PROFICIENCY_LEVELS, SKILL_CATEGORIES, STANDARD_ROLES, DEPARTMENTS
from database import (
    init_db,
    get_all_employees,
    get_employee_by_id,
    get_all_skills,
    get_skills_by_category,
    get_employee_skills,
    get_all_courses
)
from modules.assessment import (
    validate_employee_input,
    save_or_update_employee,
    save_employee_skill_assessment,
    score_diagnostic_quiz,
    DIAGNOSTIC_QUESTIONS
)
from modules.skill_gap import (
    analyze_skill_gap,
    create_radar_chart,
    create_gap_bar_chart
)
from modules.recommender import recommend_courses
from modules.roadmap import (
    generate_learning_roadmap,
    create_roadmap_timeline_chart
)
from modules.tracker import (
    enroll_employee_in_course,
    update_course_progress,
    log_learning_activity,
    get_employee_tracker_summary
)
from modules.analytics import (
    get_workforce_overview,
    create_department_readiness_chart,
    create_org_gaps_chart,
    create_talent_mobility_donut,
    create_skill_distribution_heatmap
)

# Page configuration
st.set_page_config(
    page_title="SkillPath AI | Corporate Upskilling Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Custom CSS for polished corporate UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .badge-card {
        background-color: #F1F5F9;
        border-left: 4px solid #3B82F6;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    }
    .stProgress > div > div > div > div {
        background-color: #10B981;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Active Employee Context & Navigation ---
st.sidebar.image("https://img.icons8.com/isometric/100/compass--v1.png", width=70)
st.sidebar.title("SkillPath AI")
st.sidebar.caption("Enterprise Talent Intelligence & Upskilling")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Executive Dashboard",
        "📝 Skill Assessment",
        "🎯 Skill Gap Analyzer",
        "💡 Course Recommendations",
        "🗺️ Personalized Roadmap",
        "📈 Learning Tracker",
        "📊 HR Workforce Analytics"
    ]
)

st.sidebar.markdown("---")

# Employee Context Selector
employees_df = get_all_employees()
if not employees_df.empty:
    emp_options = {
        f"{row['name']} ({row['current_role']} ➔ {row['target_role']})": row["id"]
        for _, row in employees_df.iterrows()
    }
    selected_label = st.sidebar.selectbox("Active Employee View", list(emp_options.keys()))
    current_emp_id = emp_options[selected_label]
    active_emp = get_employee_by_id(current_emp_id)

    # Sidebar Employee Profile Badge
    with st.sidebar.expander("👤 Employee Details", expanded=True):
        st.write(f"**Department:** {active_emp['department']}")
        st.write(f"**Target Role:** {active_emp['target_role']}")
        st.write(f"**Experience:** {active_emp['experience_years']} yrs")
        st.write(f"**Weekly Commitment:** {active_emp['weekly_learning_hours']} hrs/week")
else:
    active_emp = None
    current_emp_id = None

st.sidebar.markdown("---")
# Admin tools
with st.sidebar.expander("⚙️ System / Demo Controls"):
    if st.button("🔄 Reset Demo Seed Data"):
        init_db(force_reseed=True)
        st.success("Database re-seeded with realistic enterprise data!")
        st.rerun()

# -------------------------------------------------------------
# PAGE 1: EXECUTIVE DASHBOARD
# -------------------------------------------------------------
if page == "🏠 Executive Dashboard":
    st.markdown("<div class='main-header'>Welcome to SkillPath AI</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Bridging corporate capability gaps through deterministic, explainable AI-driven upskilling.</div>",
        unsafe_allow_html=True
    )

    if active_emp:
        # High level metrics for active employee
        gap_res = analyze_skill_gap(current_emp_id)
        tracker_res = get_employee_tracker_summary(current_emp_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Target Role Readiness", f"{gap_res['readiness_score']}%", 
                      delta=f"{len(gap_res['strengths'])} skills met")
        with col2:
            st.metric("Critical Skill Gaps", len(gap_res["critical_gaps"]))
        with col3:
            st.metric("Active Enrollments", tracker_res["active_courses"])
        with col4:
            st.metric("Logged Learning Time", f"{tracker_res['total_hours']} hrs")

        st.markdown("---")

        # Two-column layout: Radar Chart & Quick Actionable Recommendations
        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            st.subheader(f"Competency Radar: {active_emp['name']}")
            st.caption(f"Comparing current proficiency against benchmark for **{active_emp['target_role']}**")
            radar_fig = create_radar_chart(gap_res["gap_df"], active_emp["target_role"], active_emp["name"])
            st.plotly_chart(radar_fig, use_container_width=True)

        with col_right:
            st.subheader("Priority Action Plan")
            if gap_res["critical_gaps"]:
                st.warning(f"🚨 **{len(gap_res['critical_gaps'])} Critical Skill Gaps** require immediate intervention:")
                for cg in gap_res["critical_gaps"][:3]:
                    st.markdown(f"- **{cg['skill_name']}**: Current Lvl {cg['current_level']} ➔ Required Lvl {cg['required_level']} (*Gap: +{cg['gap']}*)")
            else:
                st.success("✅ No critical gaps detected! You are well-aligned with your target role benchmark.")

            st.markdown("#### Recommended Next Course")
            recs = recommend_courses(current_emp_id, top_n=1)
            if recs:
                top_rec = recs[0]
                st.markdown(f"**[{top_rec['title']}]({top_rec['platform_url']})**")
                st.caption(f"Provider: {top_rec['provider']} | Skill: {top_rec['skill_name']} (Lvl {top_rec['level']})")
                st.info(f"💡 {top_rec['explanation']}")
                if st.button("➕ Quick Enroll", key="dash_quick_enroll"):
                    ok, err = enroll_employee_in_course(current_emp_id, top_rec["course_id"])
                    if ok:
                        st.success(f"Enrolled in {top_rec['title']}!")
                        st.rerun()
                    else:
                        st.warning(err)

            st.markdown("#### Unlocked Achievements")
            if tracker_res["badges"]:
                badge_cols = st.columns(len(tracker_res["badges"]))
                for i, badge in enumerate(tracker_res["badges"]):
                    with badge_cols[i]:
                        st.markdown(f"### {badge['icon']}\n**{badge['title']}**\n\n<small>{badge['desc']}</small>", unsafe_allow_html=True)
            else:
                st.caption("Enroll in courses and log study hours to unlock achievements.")


# -------------------------------------------------------------
# PAGE 2: EMPLOYEE SKILL ASSESSMENT
# -------------------------------------------------------------
elif page == "📝 Skill Assessment":
    st.markdown("<div class='main-header'>Employee Skill Assessment & Diagnostic</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Assess employee competencies via self-rating or take the objective diagnostic mini-quiz to eliminate self-assessment bias.</div>",
        unsafe_allow_html=True
    )

    tab_profile, tab_self_assess, tab_quiz = st.tabs([
        "👤 Employee Profile & Registration",
        "🎚️ Self-Assessment Rating",
        "🧠 Objective Diagnostic Quiz"
    ])

    with tab_profile:
        st.subheader("Employee Details Management")
        with st.form("employee_profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                form_name = st.text_input("Full Name", value=active_emp["name"] if active_emp else "")
                form_email = st.text_input("Corporate Email", value=active_emp["email"] if active_emp else "")
                form_dept = st.selectbox(
                    "Department",
                    DEPARTMENTS,
                    index=DEPARTMENTS.index(active_emp["department"]) if active_emp and active_emp["department"] in DEPARTMENTS else 0
                )
            with col2:
                form_curr_role = st.text_input("Current Role Designation", value=active_emp["current_role"] if active_emp else "")
                form_target_role = st.selectbox(
                    "Target Aspirational Role",
                    STANDARD_ROLES,
                    index=STANDARD_ROLES.index(active_emp["target_role"]) if active_emp and active_emp["target_role"] in STANDARD_ROLES else 0
                )
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    form_exp = st.number_input("Years of Experience", min_value=0.0, max_value=50.0, value=float(active_emp["experience_years"]) if active_emp else 2.0, step=0.5)
                with sub_col2:
                    form_hours = st.number_input("Weekly Learning Hours", min_value=1.0, max_value=40.0, value=float(active_emp["weekly_learning_hours"]) if active_emp else 5.0, step=1.0)

            submitted = st.form_submit_button("💾 Save Profile")
            if submitted:
                emp_id, err = save_or_update_employee(
                    name=form_name,
                    email=form_email,
                    department=form_dept,
                    current_role=form_curr_role,
                    target_role=form_target_role,
                    experience_years=form_exp,
                    weekly_learning_hours=form_hours,
                    employee_id=current_emp_id
                )
                if err:
                    st.error(f"Validation Error: {err}")
                else:
                    st.success("Employee profile successfully updated!")
                    st.rerun()

    with tab_self_assess:
        st.subheader(f"Rate Competencies for: {active_emp['name']}")
        st.info("Scale: **1: Beginner** (Theory only) | **2: Elementary** (Assisted tasks) | **3: Intermediate** (Independent) | **4: Advanced** (Leads & designs) | **5: Expert** (Architect & innovator)")

        emp_skills_df = get_employee_skills(current_emp_id)
        current_ratings = dict(zip(emp_skills_df["skill_id"], emp_skills_df["proficiency_level"]))

        skills_by_cat = get_skills_by_category()
        updated_ratings = {}

        with st.form("self_assessment_form"):
            for category, skills_list in skills_by_cat.items():
                st.markdown(f"#### 📂 {category}")
                cols = st.columns(2)
                for i, skill in enumerate(skills_list):
                    sid = skill["id"]
                    curr_val = current_ratings.get(sid, 1)
                    # Clamping to valid range 1-5
                    curr_val = max(1, min(5, curr_val))
                    with cols[i % 2]:
                        updated_ratings[sid] = st.slider(
                            f"{skill['name']}",
                            min_value=1,
                            max_value=5,
                            value=curr_val,
                            key=f"skill_slider_{sid}",
                            help=skill["description"]
                        )
                st.markdown("---")

            if st.form_submit_button("✅ Update Self-Assessment Ratings"):
                success, err = save_employee_skill_assessment(current_emp_id, updated_ratings)
                if success:
                    st.success("Skill assessment successfully saved!")
                    st.rerun()
                else:
                    st.error(f"Error saving ratings: {err}")

    with tab_quiz:
        st.subheader("Objective Skill Diagnostic Mini-Quiz")
        st.caption("Standardized questions to objectively benchmark employee foundational competencies.")
        
        with st.form("diagnostic_quiz_form"):
            user_answers = {}
            for q in DIAGNOSTIC_QUESTIONS:
                st.markdown(f"**Q{q['id']}. [{q['category']} / {q['skill']}]** {q['question']}")
                selected_idx = st.radio(
                    "Select best answer:",
                    options=range(len(q["options"])),
                    format_func=lambda i, opts=q["options"]: opts[i],
                    key=f"quiz_q_{q['id']}"
                )
                user_answers[q["id"]] = selected_idx
                st.markdown("---")

            if st.form_submit_button("📊 Submit Diagnostic Answers"):
                quiz_result = score_diagnostic_quiz(user_answers)
                st.subheader(f"Diagnostic Score: {quiz_result['score_pct']}% ({quiz_result['correct_answers']}/{quiz_result['total_questions']} correct)")
                st.info(f"🎯 **Suggested Baseline Proficiency Level:** Level {quiz_result['suggested_baseline']} ({PROFICIENCY_LEVELS[quiz_result['suggested_baseline']]['name']})")
                
                with st.expander("Review Answer Breakdown"):
                    for b in quiz_result["breakdown"]:
                        if b["is_correct"]:
                            st.success(f"✅ **{b['skill']}**: Correct ({b['correct_option']})")
                        else:
                            st.error(f"❌ **{b['skill']}**: Your answer: '{b['selected_option']}' | Correct: '{b['correct_option']}'")


# -------------------------------------------------------------
# PAGE 3: SKILL GAP ANALYZER
# -------------------------------------------------------------
elif page == "🎯 Skill Gap Analyzer":
    st.markdown("<div class='main-header'>Target Role Skill Gap Analyzer</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='sub-header'>Evaluating <b>{active_emp['name']}</b>'s skill profile against <b>{active_emp['target_role']}</b> benchmarks.</div>",
        unsafe_allow_html=True
    )

    # Allow what-if role benchmark switching
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        target_role_eval = st.selectbox(
            "Simulate Target Role Benchmark (What-if scenario):",
            STANDARD_ROLES,
            index=STANDARD_ROLES.index(active_emp["target_role"]) if active_emp["target_role"] in STANDARD_ROLES else 0
        )

    gap_data = analyze_skill_gap(current_emp_id, target_role=target_role_eval)
    gap_df = gap_data["gap_df"]

    # Top KPI row
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Benchmark Readiness Score", f"{gap_data['readiness_score']}%")
    with kpi2:
        st.metric("Total Skills Evaluated", gap_data["total_skills_required"])
    with kpi3:
        st.metric("Critical Gaps", len(gap_data["critical_gaps"]))
    with kpi4:
        st.metric("Competencies Met", len(gap_data["strengths"]))

    st.markdown("---")

    # Visualizations
    vcol1, vcol2 = st.columns([1, 1])
    with vcol1:
        st.subheader("Competency Radar vs Role Benchmark")
        radar_fig = create_radar_chart(gap_df, target_role_eval, active_emp["name"])
        st.plotly_chart(radar_fig, use_container_width=True)

    with vcol2:
        st.subheader("Gap Severity by Competency")
        bar_fig = create_gap_bar_chart(gap_df)
        st.plotly_chart(bar_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Detailed Gap Breakdown Table")

    if not gap_df.empty:
        display_df = gap_df[["skill_name", "category", "current_level", "required_level", "gap", "is_core", "status"]].copy()
        display_df["is_core"] = display_df["is_core"].apply(lambda x: "⭐ Core" if x == 1 else "Elective")
        display_df.columns = ["Skill Name", "Category", "Current Level", "Required Benchmark", "Gap", "Role Importance", "Status"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------
# PAGE 4: COURSE RECOMMENDATION ENGINE
# -------------------------------------------------------------
elif page == "💡 Course Recommendations":
    st.markdown("<div class='main-header'>AI-Powered Course Recommendations</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Personalized course suggestions targeting identified skill gaps with transparent, explainable scoring.</div>",
        unsafe_allow_html=True
    )

    # Controls row
    rc1, rc2, rc3 = st.columns([1.5, 1.5, 1])
    with rc1:
        use_ai = st.toggle("🤖 Use AI Multi-Criteria Scoring (vs Deterministic Fallback)", value=True)
    with rc2:
        skills_df = get_all_skills()
        skill_filter = st.selectbox(
            "Filter by Specific Gap Skill",
            options=["All Gap Skills"] + list(skills_df["name"].unique())
        )
        selected_skill_id = None
        if skill_filter != "All Gap Skills":
            match = skills_df[skills_df["name"] == skill_filter]
            if not match.empty:
                selected_skill_id = int(match.iloc[0]["id"])
    with rc3:
        num_recs = st.slider("Top Recommendations", min_value=3, max_value=10, value=6)

    recs = recommend_courses(
        current_emp_id,
        use_ai_heuristic=use_ai,
        top_n=num_recs,
        filter_skill_id=selected_skill_id
    )

    if not recs:
        st.info("No courses found matching criteria.")
    else:
        st.caption(f"Showing **{len(recs)}** recommended courses sorted by relevance.")
        
        # Display course recommendation cards
        for rec in recs:
            with st.container():
                st.markdown(f"""
                <div class='badge-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h4 style='margin: 0; color: #1E3A8A;'>{rec['title']}</h4>
                        <span style='background: #E0E7FF; color: #3730A3; font-weight: 600; padding: 2px 8px; border-radius: 4px;'>
                            Fit Score: {rec['score']}
                        </span>
                    </div>
                    <p style='margin: 4px 0; color: #475569;'>
                        <b>Provider:</b> {rec['provider']} | <b>Skill:</b> {rec['skill_name']} (Level {rec['level']}/5) | <b>Duration:</b> {rec['duration_hours']} hrs (~{rec['estimated_weeks']} wks) | <b>Rating:</b> ⭐ {rec['rating']}/5.0
                    </p>
                    <p style='margin: 6px 0; color: #334155; font-size: 0.95rem;'>
                        {rec['description']}
                    </p>
                    <p style='margin: 4px 0; color: #047857; font-weight: 500;'>
                        💡 <b>Why Recommended:</b> {rec['explanation']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                col_btn1, col_btn2, _ = st.columns([1.5, 2, 5])
                with col_btn1:
                    st.link_button("🔗 View Official Course", rec["platform_url"])
                with col_btn2:
                    if st.button("➕ Enroll Now", key=f"rec_enroll_{rec['course_id']}"):
                        ok, err = enroll_employee_in_course(current_emp_id, rec["course_id"])
                        if ok:
                            st.success(f"Enrolled in {rec['title']}!")
                            st.rerun()
                        else:
                            st.warning(err)
                st.markdown("<br>", unsafe_allow_html=True)


# -------------------------------------------------------------
# PAGE 5: PERSONALIZED LEARNING ROADMAP
# -------------------------------------------------------------
elif page == "🗺️ Personalized Roadmap":
    st.markdown("<div class='main-header'>Personalized Upskilling Roadmap</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='sub-header'>Structured learning trajectory for <b>{active_emp['name']}</b> at <b>{active_emp['weekly_learning_hours']} hrs/week</b>.</div>",
        unsafe_allow_html=True
    )

    roadmap = generate_learning_roadmap(current_emp_id)

    # Roadmap Metrics Row
    rcol1, rcol2, rcol3, rcol4 = st.columns(4)
    with rcol1:
        st.metric("Total Recommended Modules", roadmap["total_courses"])
    with rcol2:
        st.metric("Total Learning Commitment", f"{roadmap['total_hours']} hrs")
    with rcol3:
        st.metric("Estimated Program Timeline", f"{roadmap['total_weeks']} weeks")
    with rcol4:
        st.metric("Weekly Study Pace", f"{roadmap['weekly_hours']} hrs/wk")

    st.markdown("---")

    # Gantt Timeline Chart
    st.subheader("Interactive Roadmap Timeline (Gantt)")
    timeline_fig = create_roadmap_timeline_chart(roadmap)
    st.plotly_chart(timeline_fig, use_container_width=True)

    st.markdown("---")

    # Phased Breakdown Cards
    st.subheader("Sequential Program Milestones")
    for phase_name, milestone_list in roadmap["phases"].items():
        st.markdown(f"### {phase_name}")
        for m in milestone_list:
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                st.markdown(f"**Step {m['step']}: [{m['title']}]({m['platform_url']})**")
                st.caption(f"Skill: {m['skill_name']} | Provider: {m['provider']} | Study: {m['duration_hours']} hrs (~{m['weeks_duration']} weeks)")
                st.markdown(f"*Target Schedule:* **{m['start_date']}** to **{m['end_date']}**")
                st.info(f"💡 {m['explanation']}")
            with col_m2:
                if st.button("➕ Enroll in Module", key=f"road_enroll_{m['course_id']}"):
                    ok, err = enroll_employee_in_course(current_emp_id, m["course_id"])
                    if ok:
                        st.success(f"Enrolled in {m['title']}!")
                        st.rerun()
                    else:
                        st.warning(err)
            st.markdown("---")


# -------------------------------------------------------------
# PAGE 6: LEARNING PROGRESS TRACKER
# -------------------------------------------------------------
elif page == "📈 Learning Tracker":
    st.markdown("<div class='main-header'>Employee Learning Progress Tracker</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='sub-header'>Track active courses, log study hours, and earn auto-skill promotions for <b>{active_emp['name']}</b>.</div>",
        unsafe_allow_html=True
    )

    tracker_data = get_employee_tracker_summary(current_emp_id)

    # Top tracker metrics
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Enrolled Courses", tracker_data["total_enrollments"])
    with t2:
        st.metric("Completed Courses", tracker_data["completed_courses"])
    with t3:
        st.metric("Total Hours Invested", f"{tracker_data['total_hours']} hrs")
    with t4:
        st.metric("Avg Course Completion", f"{tracker_data['avg_progress']}%")

    st.markdown("---")

    col_track_left, col_track_right = st.columns([1.8, 1])

    with col_track_left:
        st.subheader("Current Enrollments & Progress")
        enrollments_df = tracker_data["enrollments_df"]

        if enrollments_df.empty:
            st.info("No active course enrollments yet. Visit 'Course Recommendations' or 'Personalized Roadmap' to enroll!")
        else:
            for _, enroll in enrollments_df.iterrows():
                cid = enroll["course_id"]
                st.markdown(f"#### [{enroll['title']}]({enroll['platform_url']})")
                st.caption(f"Skill: **{enroll['skill_name']}** | Status: **{enroll['status'].replace('_', ' ').title()}** | Enrolled: {enroll['enrolled_date']}")
                
                # Progress Bar
                st.progress(enroll["progress_pct"] / 100.0)

                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    new_prog = st.slider(
                        f"Update Progress (%)",
                        min_value=0,
                        max_value=100,
                        value=int(enroll["progress_pct"]),
                        key=f"slider_prog_{cid}"
                    )
                with col_p2:
                    if st.button("Update Progress", key=f"btn_prog_{cid}"):
                        ok, err, notif = update_course_progress(current_emp_id, cid, new_prog)
                        if ok:
                            if notif:
                                st.balloons()
                                st.success(notif)
                            else:
                                st.success(f"Progress updated to {new_prog}%!")
                            st.rerun()
                        else:
                            st.error(err)
                st.markdown("---")

    with col_track_right:
        st.subheader("Log Study Session")
        if not enrollments_df.empty:
            with st.form("log_study_form"):
                course_map = dict(zip(enrollments_df["title"], enrollments_df["course_id"]))
                selected_course_title = st.selectbox("Select Enrolled Course", list(course_map.keys()))
                hours_input = st.number_input("Study Time (Hours)", min_value=0.5, max_value=20.0, value=2.0, step=0.5)
                notes_input = st.text_area("Learning Notes / Summary", placeholder="Key topics reviewed, code built, or concepts mastered...")
                
                if st.form_submit_button("📝 Record Study Activity"):
                    cid_selected = course_map[selected_course_title]
                    ok, err = log_learning_activity(current_emp_id, cid_selected, hours_input, notes_input)
                    if ok:
                        st.success(f"Logged {hours_input} hrs for {selected_course_title}!")
                        st.rerun()
                    else:
                        st.error(err)
        else:
            st.caption("Enroll in a course first to record study logs.")

        st.markdown("#### Unlocked Badges")
        for b in tracker_data["badges"]:
            st.markdown(f"**{b['icon']} {b['title']}**: {b['desc']}")

        if tracker_data["recent_logs"]:
            st.markdown("#### Recent Activity Logs")
            for rlog in tracker_data["recent_logs"]:
                st.caption(f"⏱️ **{rlog['hours_spent']} hrs** on *{rlog['course_title']}* ({rlog['logged_at']})")
                if rlog["notes"]:
                    st.write(f"> {rlog['notes']}")


# -------------------------------------------------------------
# PAGE 7: HR WORKFORCE ANALYTICS
# -------------------------------------------------------------
elif page == "📊 HR Workforce Analytics":
    st.markdown("<div class='main-header'>HR Workforce Talent Intelligence</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='sub-header'>Company-wide skill distribution, department benchmark readiness, and organizational skill deficits.</div>",
        unsafe_allow_html=True
    )

    overview = get_workforce_overview()

    # Macro KPIs
    hkpi1, hkpi2, hkpi3, hkpi4 = st.columns(4)
    with hkpi1:
        st.metric("Total Workforce Tracked", overview["total_employees"])
    with hkpi2:
        st.metric("Company Avg Skill Readiness", f"{overview['avg_readiness']}%")
    with hkpi3:
        st.metric("Cumulative Training Hours", f"{overview['overall_training_hours']} hrs")
    with hkpi4:
        st.metric("Total Active Course Enrollments", overview["total_enrollments"])

    st.markdown("---")

    # Row 1 Charts: Department Readiness & Talent Mobility
    col_hr1, col_hr2 = st.columns([1.3, 1])
    with col_hr1:
        st.subheader("Departmental Upskilling Readiness (%)")
        dept_fig = create_department_readiness_chart(overview["department_metrics"])
        st.plotly_chart(dept_fig, use_container_width=True)

    with col_hr2:
        st.subheader("Talent Mobility Proportions")
        mobility_fig = create_talent_mobility_donut(overview["employee_readiness_df"])
        st.plotly_chart(mobility_fig, use_container_width=True)

    st.markdown("---")

    # Row 2 Charts: Top Org Skill Gaps & Skill Heatmap
    col_hr3, col_hr4 = st.columns([1, 1.3])
    with col_hr3:
        st.subheader("Top Critical Organizational Skill Gaps")
        gaps_fig = create_org_gaps_chart(overview["top_org_gaps"])
        st.plotly_chart(gaps_fig, use_container_width=True)

    with col_hr4:
        st.subheader("Departmental Skill Proficiency Heatmap")
        heatmap_fig = create_skill_distribution_heatmap()
        st.plotly_chart(heatmap_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Employee Talent Mobility Index Table")
    if not overview["employee_readiness_df"].empty:
        st.dataframe(
            overview["employee_readiness_df"][["name", "department", "current_role", "target_role", "readiness_score", "critical_gap_count", "mobility_status"]],
            use_container_width=True,
            hide_index=True
        )
