
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from src.auth_database import (
    initialize_database,
    register_user,
    login_user
)
from bs4 import BeautifulSoup
import re
import html
from src.admin_dashboard import (
    get_dashboard_stats,
    get_daily_job_counts,
    get_all_users,
    update_user_status
)
from src.ai_assistant import get_ai_response

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="MySpace | Discover Your Future",
    page_icon="🚀",
    layout="wide"
)

DB_PATH = Path(__file__).parent / "data" / "fresher_jobs.db"


def render_ai_assistant():
    st.title("🤖 MySpace AI Assistant")
    st.caption("Your personal assistant for jobs, career guidance and interview preparation.")

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    col1, col2 = st.columns([5, 1])

    with col1:
        st.markdown("### Ask me anything about your career")

    with col2:
        if st.button("🗑️ Clear chat"):
            st.session_state.ai_chat_history = []
            st.session_state.pop("ai_pending_prompt", None)
            st.rerun()

    history = st.session_state.ai_chat_history

    # Suggested prompts for a new conversation
    if not history:
        st.write("Here are a few things you can ask:")

        suggestions = [
            "Find Python internship opportunities in Bangalore.",
            "What skills should I learn to become an AI Engineer?",
            "Help me prepare for a software engineering interview.",
            "Explain the responsibilities of a Data Analyst."
        ]

        for i in range(0, len(suggestions), 2):
            cols = st.columns(2)

            for j, col in enumerate(cols):
                index = i + j
                if index < len(suggestions):
                    with col:
                        if st.button(suggestions[index], key=f"ai_suggestion_{index}"):
                            st.session_state.ai_pending_prompt = suggestions[index]
                            st.rerun()

    # Display previous messages
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Read a suggested prompt or a message typed by the user
    prompt = st.session_state.pop("ai_pending_prompt", None)

    if not prompt:
        prompt = st.chat_input("Ask about jobs, skills, careers or interviews...")

    if prompt:
        previous_history = history.copy()

        st.session_state.ai_chat_history.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("MySpace AI is thinking..."):
                response = get_ai_response(
                    prompt,
                    conversation_history=previous_history
                )

            st.markdown(response)

        st.session_state.ai_chat_history.append({
            "role": "assistant",
            "content": response
        })

# ---------------- LIGHT THEME & CUSTOM DESIGN ----------------

st.markdown("""
<style>

/* Main page */
.stApp {
    background: #f6f8ff;
    color: #1e293b;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* General typography */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: #1e293b;
}

h1, h2, h3, p, label {
    color: #1e293b;
}

/* Hero section */
.hero {
    background: linear-gradient(120deg, #dbeafe 0%, #ede9fe 55%, #fce7f3 100%);
    padding: 42px 40px;
    border-radius: 24px;
    margin-bottom: 28px;
    border: 1px solid #e0e7ff;
    position: relative;
}

.hero-title {
    font-size: 42px;
    font-weight: 800;
    color: #172554;
    margin-bottom: 8px;
    letter-spacing: -1.5px;
}

.hero-subtitle {
    font-size: 17px;
    color: #475569;
    margin-bottom: 18px;
}

.hero-tag {
    display: inline-block;
    background: rgba(255,255,255,0.75);
    color: #4338ca;
    padding: 7px 14px;
    border-radius: 30px;
    font-size: 13px;
    font-weight: 600;
}

/* Section heading */
.section-heading {
    font-size: 23px;
    font-weight: 750;
    color: #172554;
    margin-top: 12px;
    margin-bottom: 5px;
}

.section-subtitle {
    color: #64748b;
    font-size: 14px;
    margin-bottom: 20px;
}

/* Search input */
div[data-testid="stTextInput"] input {
    background: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #dbe3f0 !important;
    border-radius: 12px !important;
    min-height: 48px;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #94a3b8 !important;
}

/* Select boxes */
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: #ffffff !important;
    border: 1px solid #dbe3f0 !important;
    border-radius: 12px !important;
    color: #1e293b !important;
}

div[data-testid="stSelectbox"] * {
    color: #1e293b;
}

/* Job cards */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 17px;
    padding: 15px;
    box-shadow: 0 5px 18px rgba(30, 64, 175, 0.045);
    transition: 0.2s ease;
}

/* Job title */
.job-title {
    color: #172554;
    font-size: 20px;
    font-weight: 750;
    margin-bottom: 5px;
}

/* Company name */
.job-company {
    color: #64748b;
    font-size: 15px;
    font-weight: 500;
    margin-bottom: 13px;
}

/* Tags */
.job-tag {
    display: inline-block;
    background: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #dbeafe;
    padding: 6px 11px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 8px;
}

/* Apply button */
.stLinkButton a {
    background: linear-gradient(90deg, #2563eb, #6366f1) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    padding: 8px 18px !important;
}

.stLinkButton a:hover {
    background: linear-gradient(90deg, #1d4ed8, #4f46e5) !important;
    color: #ffffff !important;
}

/* Expanders */
div[data-testid="stExpander"] {
    background: #f8faff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
}

div[data-testid="stExpander"] summary {
    color: #334155 !important;
}

/* Results count */
.result-count {
    color: #475569;
    font-size: 15px;
    margin: 15px 0;
}

.result-number {
    color: #4f46e5;
    font-weight: 800;
}

/* Footer */
.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 13px;
    padding: 25px 0 5px;
}

/* Dividers */
hr {
    border-color: #e2e8f0;
}

</style>
""", unsafe_allow_html=True)

# ---------------- AUTHENTICATION ----------------

initialize_database()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:

    st.markdown("""
    <div class="hero">
        <div class="hero-title">Welcome to MySpace 🚀</div>
        <div class="hero-subtitle">
            Your journey towards your dream career starts here.
            Sign in or create an account to explore opportunities.
        </div>
        <span class="hero-tag">✨ Built for Freshers</span>
        <span class="hero-tag">💼 Jobs & Internships</span>
    </div>
    """, unsafe_allow_html=True)

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "✨ Create Account"]
    )

    with login_tab:

        st.markdown("### Welcome back!")
        st.write("Log in to continue exploring opportunities.")

        with st.form("login_form"):

            email = st.text_input(
                "Email address",
                placeholder="Enter your email"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )

            login_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if login_button:

                if not email.strip() or not password:
                    st.error("Please enter your email and password.")

                else:
                    user = login_user(email, password)

                    if user:
                        st.session_state.user = user
                        st.rerun()

                    else:
                        st.error("Invalid email or password.")

    with register_tab:

        st.markdown("### Create your account")
        st.write("Join MySpace and discover your next opportunity.")

        with st.form("register_form"):

            full_name = st.text_input(
                "Full name",
                placeholder="Enter your full name"
            )

            email = st.text_input(
                "Email address",
                placeholder="Enter your email"
            )

            password = st.text_input(
                "Create password",
                type="password",
                placeholder="Minimum 8 characters"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            register_button = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if register_button:

                if not full_name.strip() or not email.strip():
                    st.error("Please fill in all required fields.")

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                else:
                    success, message = register_user(
                        full_name,
                        email,
                        password
                    )

                    if success:
                        st.success(message)

                        st.session_state.user = login_user(
                            email,
                            password
                        )

                        st.rerun()

                    else:
                        st.error(message)

    st.stop()


# ---------------- LOGGED-IN USER ----------------

current_user = st.session_state.user

# ---------------- ADMIN DASHBOARD ----------------

if current_user["role"] == "admin":

    st.sidebar.markdown("## 🚀 MySpace Admin")
    st.sidebar.caption(f"Administrator: {current_user['full_name']}")
    st.sidebar.divider()

    admin_page = st.sidebar.radio(
        "ADMIN MENU",
        [
            "Dashboard",
            "Job Management",
            "User Management",
            "Daily Analytics",
            "AI Assistant"
        ]
    )

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

    st.markdown("""
    <div class="hero">
        <div class="hero-title">Admin Dashboard 👋</div>
        <div class="hero-subtitle">
            Monitor your jobs, users and platform activity from one place.
        </div>
        <span class="hero-tag">⚙️ Platform Administration</span>
        <span class="hero-tag">📊 Live Database Statistics</span>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- DASHBOARD OVERVIEW ----------------

    if admin_page == "Dashboard":

        st.subheader("Platform Overview")

        stats = get_dashboard_stats()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Jobs", stats["total_jobs"])
        col2.metric("Registered Users", stats["total_users"])
        col3.metric("Jobs Added Today", stats["jobs_today"])
        col4.metric("Active Users", stats["active_users"])

        st.divider()

        st.subheader("Recent Job Collection Activity")

        daily_data = get_daily_job_counts()

        if not daily_data.empty:
            chart_data = daily_data.set_index("job_date")
            st.bar_chart(chart_data["jobs_added"])
        else:
            st.info("No job collection history available yet.")

        st.caption(
            "Active users are users who logged in during the last 30 days."
        )

    # ---------------- JOB MANAGEMENT ----------------

    elif admin_page == "Job Management":

        st.subheader("Job Management")

        jobs_conn = sqlite3.connect(DB_PATH)

        job_df = pd.read_sql_query("""
            SELECT
                id,
                job_title,
                company,
                location,
                experience_level,
                source,
                created_at
            FROM fresher_jobs
            ORDER BY id DESC
        """, jobs_conn)

        jobs_conn.close()

        st.write(f"Total listings: **{len(job_df)}**")

        job_search = st.text_input(
            "Search jobs",
            placeholder="Search by title or company..."
        )

        if job_search:
            mask = (
                job_df["job_title"].fillna("").str.contains(
                    job_search, case=False
                )
                |
                job_df["company"].fillna("").str.contains(
                    job_search, case=False
                )
            )

            job_df = job_df[mask]

        st.dataframe(
            job_df,
            use_container_width=True,
            hide_index=True
        )

    # ---------------- USER MANAGEMENT ----------------

    elif admin_page == "User Management":

        st.subheader("User Management")

        users = get_all_users()

        if users:

            users_df = pd.DataFrame(users)

            st.write(f"Registered accounts: **{len(users_df)}**")

            st.dataframe(
                users_df.drop(columns=["id"]),
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.markdown("### Manage user access")

            manageable_users = [
                user for user in users
                if user["role"] != "admin"
            ]

            if manageable_users:

                selected_user = st.selectbox(
                    "Select a user",
                    manageable_users,
                    format_func=lambda user: (
                        f"{user['full_name']} ({user['email']})"
                    )
                )

                if selected_user["is_active"]:

                    st.success("This account is active.")

                    if st.button("Deactivate User"):
                        changed = update_user_status(
                            selected_user["id"],
                            False
                        )

                        if changed:
                            st.success("User account deactivated.")
                            st.rerun()
                        else:
                            st.error("Unable to update this account.")

                else:

                    st.warning("This account is inactive.")

                    if st.button("Reactivate User"):
                        changed = update_user_status(
                            selected_user["id"],
                            True
                        )

                        if changed:
                            st.success("User account reactivated.")
                            st.rerun()
                        else:
                            st.error("Unable to update this account.")

            else:
                st.info("There are no regular user accounts to manage.")

        else:
            st.info("No registered users found.")

    # ---------------- DAILY ANALYTICS ----------------

    elif admin_page == "Daily Analytics":

        st.subheader("Daily Job Analytics")

        daily_data = get_daily_job_counts()

        if not daily_data.empty:

            st.markdown("### Jobs added per day")

            st.bar_chart(
                daily_data.set_index("job_date")["jobs_added"]
            )

            st.markdown("### Collection history")

            st.dataframe(
                daily_data,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No daily job data available.")

    elif admin_page == "AI Assistant":
        render_ai_assistant()

    st.stop()


# ---------------- NORMAL USER SIDEBAR ----------------


with st.sidebar:

    st.markdown("## 🚀 MySpace")

    st.write(f"Welcome, **{current_user['full_name']}**")

    st.caption(current_user["email"])

    st.divider()

    st.write("👤 Job Seeker Account")
    user_page = st.radio(
    "NAVIGATION",
    ["Find Jobs", "AI Assistant"],
    key="user_navigation"
    )


    if st.button("Logout", use_container_width=True):

        st.session_state.user = None
        st.rerun()

# ---------------- DATABASE ----------------

@st.cache_data(ttl=60)
def load_jobs():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT
        id,
        job_title,
        company,
        location,
        job_description,
        job_url,
        experience_level,
        min_experience,
        max_experience,
        classification_source,
        created_at,
        is_shortlisted,
        shortlist_score
    FROM fresher_jobs
    WHERE is_shortlisted = 1
    ORDER BY shortlist_score DESC, id DESC
        """,
        conn
    )

    conn.close()
    return df




def clean_job_description(description):

    if pd.isna(description):
        return "Job description is not available."

    description = html.unescape(str(description))

    soup = BeautifulSoup(description, "html.parser")

    # Preserve readable paragraph and list formatting
    for tag in soup.find_all(["br"]):
        tag.replace_with("\n")

    for tag in soup.find_all(["p", "div", "section"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    for tag in soup.find_all("li"):
        tag.insert_before("\n• ")

    clean_text = soup.get_text(separator=" ", strip=True)

    clean_text = re.sub(r"[ \t]+", " ", clean_text)
    clean_text = re.sub(r"\n\s*\n+", "\n\n", clean_text)

    return clean_text.strip()

# ---------------- CITY NORMALIZATION ----------------

CITY_OPTIONS = [
    "Bangalore",
    "Mumbai",
    "Pune",
    "Delhi",
    "Kolkata",
    "Gurugram",
    "Remote (India)"
]


def normalize_city(location):

    if pd.isna(location):
        return None

    loc = str(location).lower().strip()

    if "remote" in loc and (
        "india" in loc or loc == "remote"
    ):
        return "Remote (India)"

    if any(word in loc for word in [
        "bangalore", "bengaluru", "banglore"
    ]):
        return "Bangalore"

    if "mumbai" in loc:
        return "Mumbai"

    if "pune" in loc:
        return "Pune"

    if "delhi" in loc or "new delhi" in loc:
        return "Delhi"

    if "kolkata" in loc or "calcutta" in loc:
        return "Kolkata"

    if "gurugram" in loc or "gurgaon" in loc:
        return "Gurugram"

    return None


# ---------------- HERO SECTION ----------------
if user_page == "AI Assistant":
    render_ai_assistant()

    st.stop()
st.markdown("""
<div class="hero">
    <div class="hero-title">Your Career Starts Here. 🚀</div>
    <div class="hero-subtitle">
        Explore opportunities, discover your potential
        and take the first step towards your dream career.
    </div>
    <span class="hero-tag">✨ Built for Freshers</span>
    <span class="hero-tag">💼 Jobs & Internships</span>
    <span class="hero-tag">🇮🇳 Opportunities Across India</span>
</div>
""", unsafe_allow_html=True)


# ---------------- LOAD DATA ----------------

try:
    jobs = load_jobs()

except Exception as e:
    st.error(f"Unable to load jobs: {e}")
    st.stop()

if jobs.empty:
    st.warning("No opportunities available right now.")
    st.stop()



# Normalize locations
jobs["city"] = jobs["location"].apply(normalize_city)


# ---------------- SEARCH SECTION ----------------

st.markdown(
    '<div class="section-heading">Find your opportunity</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Search for jobs that match your interests and preferred location.'
    '</div>',
    unsafe_allow_html=True
)

search = st.text_input(
    "Search jobs",
    placeholder="🔍  Search by job title or company..."
)

col1, col2 = st.columns(2)

with col1:
    selected_city = st.selectbox(
        "📍 Preferred City",
        ["All Cities"] + CITY_OPTIONS
    )

with col2:
    job_types = sorted(
        jobs["experience_level"]
        .dropna()
        .unique()
        .tolist()
    )

    job_types = [
        item for item in job_types
        if item.strip().lower() != "unclear"
    ]

    selected_type = st.selectbox(
        "💼 Opportunity Type",
        ["All Types"] + job_types
    )


# ---------------- FILTER JOBS ----------------

filtered_jobs = jobs.copy()

if search:
    search_mask = (
        filtered_jobs["job_title"]
        .fillna("")
        .str.contains(search, case=False, na=False)
        |
        filtered_jobs["company"]
        .fillna("")
        .str.contains(search, case=False, na=False)
    )

    filtered_jobs = filtered_jobs[search_mask]

if selected_city != "All Cities":
    filtered_jobs = filtered_jobs[
        filtered_jobs["city"] == selected_city
    ]

if selected_type != "All Types":
    filtered_jobs = filtered_jobs[
        filtered_jobs["experience_level"] == selected_type
    ]


# ---------------- RESULTS ----------------

st.divider()

st.markdown(
    f'<div class="result-count">'
    f'✨ Showing <span class="result-number">'
    f'{len(filtered_jobs)}</span> opportunities'
    f'</div>',
    unsafe_allow_html=True
)


if filtered_jobs.empty:

    st.info(
        "No matching opportunities found. "
        "Try changing your search or filters."
    )

else:

    for _, job in filtered_jobs.iterrows():

        with st.container(border=True):

            st.markdown(
                f'<div class="job-title">{job["job_title"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="job-company">🏢 '
                f'{job["company"]}</div>',
                unsafe_allow_html=True
            )

            city = job["city"] or "Other location"

            min_exp = job["min_experience"]
            max_exp = job["max_experience"]

            if pd.notna(min_exp) and pd.notna(max_exp):
                experience = f"{min_exp:g}–{max_exp:g} years"

            elif pd.notna(min_exp):
                experience = f"{min_exp:g}+ years"

            else:
                experience = "Not specified"

            st.markdown(
                f'<span class="job-tag">📍 {city}</span>'
                f'<span class="job-tag">💼 '
                f'{job["experience_level"] or "Not specified"}</span>'
                f'<span class="job-tag">⏳ {experience}</span>',
                unsafe_allow_html=True
            )
            if job["classification_source"] in ["Python", "Groq"]:
                st.success("Experience classified")
            else:
                st.warning("Shortlisted – eligibility review pending")

            with st.expander("View job description"):

                description = job["job_description"]

                if pd.notna(description) and str(description).strip():
                    st.text(clean_job_description(description))

                else:
                    st.info("Job description is not available.")

            if pd.notna(job["job_url"]) and str(job["job_url"]).strip():
                st.link_button(
                    "Apply Now ↗",
                    str(job["job_url"])
                )


# ---------------- FOOTER ----------------

st.markdown("""
<div class="footer">
    Made with 💙 for the next generation of professionals.
    <br>
    © MySpace | Discover. Explore. Grow.
</div>
""", unsafe_allow_html=True)
