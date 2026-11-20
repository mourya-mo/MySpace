
import streamlit as st
import sqlite3
import pandas as pd
import html
import re

from pathlib import Path
from bs4 import BeautifulSoup

from src.auth_database import (
    initialize_database,
    register_user,
    login_user
)

from src.admin_dashboard import (
    get_dashboard_stats,
    get_daily_job_counts,
    get_all_users,
    update_user_status
)

from src.ai_assistant import get_ai_response

from src.chat_history import (
    initialize_chat_tables,
    create_chat,
    get_user_chats,
    get_chat_messages,
    save_chat_message,
    update_chat_title,
    delete_chat
)


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MySpace | Discover Your Future",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "fresher_jobs.db"


# =========================================================
# COMPLETE APPLICATION THEME
# =========================================================

st.markdown("""
<style>

/* MAIN APPLICATION */

.stApp {
    background-color: #f4f7fc;
    color: #24344d;
}

[data-testid="stAppViewContainer"] {
    background-color: #f4f7fc;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1250px;
}

/* MAIN PAGE TEXT */

[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] .stMarkdown {
    color: #24344d;
}

[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
    color: #14233d;
}

/* SIDEBAR BACKGROUND */

[data-testid="stSidebar"] {
    background-color: #101d35 !important;
    border-right: 1px solid #263957 !important;
}

[data-testid="stSidebar"] > div:first-child {
    background-color: #101d35 !important;
}

/* SIDEBAR TEXT */

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] .stRadio,
[data-testid="stSidebar"] .stRadio *,
[data-testid="stSidebar"] [role="radiogroup"],
[data-testid="stSidebar"] [role="radiogroup"] * {
    color: #ffffff !important;
}

/* SIDEBAR RADIO NAVIGATION */

[data-testid="stSidebar"] [role="radio"] {
    color: #ffffff !important;
}

[data-testid="stSidebar"] [role="radio"] p {
    color: #ffffff !important;
}

[data-testid="stSidebar"] [role="radio"] div {
    color: #ffffff !important;
}

/* SIDEBAR INPUTS */

[data-testid="stSidebar"] input {
    background-color: #ffffff !important;
    color: #17243b !important;
    -webkit-text-fill-color: #17243b !important;
}

/* SIDEBAR BUTTONS */

[data-testid="stSidebar"] .stButton button {
    background-color: #1d5c96 !important;
    color: #ffffff !important;
    border: 1px solid #3b78ad !important;
    border-radius: 9px;
}

[data-testid="stSidebar"] .stButton button p {
    color: #ffffff !important;
}

/* SIDEBAR DIVIDERS */

[data-testid="stSidebar"] hr {
    border-color: #34445d !important;
}

/* HERO SECTION */

.hero {
    background: linear-gradient(
        120deg,
        #122644 0%,
        #1d4776 65%,
        #246b91 100%
    );
    padding: 36px;
    border-radius: 18px;
    margin-bottom: 28px;
    color: white;
    box-shadow: 0 8px 25px rgba(20, 40, 75, 0.12);
}

.hero-title {
    color: #ffffff !important;
    font-size: 34px;
    font-weight: 750;
    margin-bottom: 10px;
}

.hero-subtitle {
    color: #dce8f7 !important;
    font-size: 16px;
    line-height: 1.7;
    max-width: 720px;
}

.hero-tag {
    display: inline-block;
    color: #ffffff !important;
    background: rgba(255,255,255,0.12);
    padding: 7px 13px;
    border-radius: 20px;
    margin: 18px 7px 0 0;
    font-size: 12px;
}

/* CARDS */

[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border: 1px solid #e2e9f3;
    border-radius: 14px;
}

/* BUTTONS */

.stButton button,
.stFormSubmitButton button,
.stLinkButton a {
    background: #1d5c96;
    color: #ffffff !important;
    border: none;
    border-radius: 9px;
    font-weight: 600;
    transition: 0.2s ease;
}

.stButton button p {
    color: #ffffff !important;
}

.stButton button:hover,
.stFormSubmitButton button:hover,
.stLinkButton a:hover {
    background: #143f6c;
    color: #ffffff !important;
}

/* INPUTS */

.stTextInput input,
.stTextArea textarea {
    border-radius: 9px;
    border-color: #d5dfec;
    background-color: #ffffff;
    color: #17243b !important;
    -webkit-text-fill-color: #17243b !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #718096 !important;
    -webkit-text-fill-color: #718096 !important;
}

/* SELECT BOX */

[data-baseweb="select"] * {
    color: #17243b !important;
}

/* METRICS */

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e1e9f3;
    border-radius: 13px;
    padding: 18px;
}

[data-testid="stMetricValue"] {
    color: #1d5c96;
}

/* JOB CARDS */

.job-title {
    color: #142d4d !important;
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 5px;
}

.job-company {
    color: #52657f !important;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 14px;
}

.job-tag {
    display: inline-block;
    background: #edf3fa;
    color: #24476d !important;
    padding: 6px 11px;
    border-radius: 20px;
    margin: 3px 5px 8px 0;
    font-size: 12px;
}

/* CHAT */

[data-testid="stChatMessage"] {
    background: #ffffff;
    border: 1px solid #e5ebf3;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 12px;
}

[data-testid="stChatMessage"] p {
    color: #24344d !important;
}

[data-testid="stChatInput"] {
    border-radius: 12px;
}

/* EXPANDER */

[data-testid="stExpander"] {
    border: 1px solid #dce5f0;
    border-radius: 10px;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    color: #24344d !important;
}

/* TABLES */

[data-testid="stDataFrame"] {
    background: #ffffff;
}

/* FOOTER */

.footer {
    text-align: center;
    color: #718096 !important;
    padding: 28px 10px;
    font-size: 13px;
    margin-top: 35px;
}

/* DIVIDERS */

hr {
    border-color: #e1e8f1;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

initialize_database()
initialize_chat_tables()


# =========================================================
# SESSION STATE
# =========================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

if "pending_chat_prompt" not in st.session_state:
    st.session_state.pending_chat_prompt = None


# =========================================================
# COMMON FUNCTIONS
# =========================================================

def logout():
    st.session_state.user = None
    st.session_state.active_chat_id = None
    st.session_state.pending_chat_prompt = None
    st.rerun()


def render_footer():
    st.markdown("""
    <div class="footer">
        Made with 💙 for the next generation of professionals.
        <br>
        © MySpace | Discover. Explore. Grow.
    </div>
    """, unsafe_allow_html=True)


def render_hero(title, subtitle, tags=None):

    tag_html = ""

    if tags:
        tag_html = "".join(
            f'<span class="hero-tag">{html.escape(tag)}</span>'
            for tag in tags
        )

    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{html.escape(title)}</div>
        <div class="hero-subtitle">{html.escape(subtitle)}</div>
        {tag_html}
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# LOGIN AND REGISTRATION
# =========================================================

if st.session_state.user is None:

    render_hero(
        "Welcome to MySpace 🚀",
        "Your journey towards your dream career starts here. "
        "Sign in or create an account to explore opportunities.",
        [
            "✨ Built for Freshers",
            "💼 Jobs & Internships",
            "🇮🇳 Opportunities Across India"
        ]
    )

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "✨ Create Account"]
    )

    with login_tab:

        st.subheader("Welcome back!")
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

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if submitted:

                if not email.strip() or not password:
                    st.error("Please enter your email and password.")

                else:

                    user = login_user(email, password)

                    if user:
                        st.session_state.user = user
                        st.session_state.active_chat_id = None
                        st.rerun()

                    else:
                        st.error("Invalid email or password.")

    with register_tab:

        st.subheader("Create your account")
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

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if submitted:

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

    render_footer()
    st.stop()


# =========================================================
# CURRENT USER
# =========================================================

current_user = st.session_state.user
user_id = current_user["id"]
is_admin = current_user["role"] == "admin"


# =========================================================
# AI ASSISTANT WITH PER-USER CHAT HISTORY
# =========================================================

def render_ai_assistant():

    st.title("MySpace AI Assistant")

    st.caption(
        "Your personal assistant for jobs, career guidance "
        "and interview preparation."
    )

    st.divider()

    chats = get_user_chats(user_id)

    chat_ids = [chat["id"] for chat in chats]

    if st.session_state.active_chat_id not in chat_ids:
        st.session_state.active_chat_id = None

    # CHAT HISTORY SIDEBAR

    with st.sidebar:

        st.markdown("### 💬 Your Conversations")

        if st.button(
            "＋ New Chat",
            use_container_width=True,
            key="new_chat_button"
        ):

            new_id = create_chat(user_id)

            st.session_state.active_chat_id = new_id
            st.session_state.pending_chat_prompt = None

            st.rerun()

        st.divider()

        if not chats:
            st.caption("Your conversations will appear here.")

        for chat in chats:

            chat_id = chat["id"]
            title = chat["title"]

            col1, col2 = st.columns([5, 1])

            with col1:

                if st.button(
                    title,
                    key=f"open_chat_{chat_id}",
                    use_container_width=True
                ):

                    st.session_state.active_chat_id = chat_id
                    st.session_state.pending_chat_prompt = None

                    st.rerun()

            with col2:

                if st.button(
                    "🗑",
                    key=f"delete_chat_{chat_id}"
                ):

                    delete_chat(chat_id, user_id)

                    if st.session_state.active_chat_id == chat_id:
                        st.session_state.active_chat_id = None

                    st.rerun()

        st.divider()

        st.caption("Your conversations are private to your account.")

    # CREATE OR SELECT CHAT

    if st.session_state.active_chat_id is None:

        if chats:
            st.session_state.active_chat_id = chats[0]["id"]

        else:
            st.session_state.active_chat_id = create_chat(user_id)

        st.rerun()

    active_chat_id = st.session_state.active_chat_id

    messages = get_chat_messages(active_chat_id, user_id)

    # EMPTY CHAT SCREEN

    if not messages:

        st.markdown("### 👋 How can I help you today?")

        st.write(
            "Ask me about job opportunities, skills, "
            "interviews, resumes or career planning."
        )

        suggestions = [
            "Find Python internship opportunities in Bangalore.",
            "What skills should I learn to become an AI Engineer?",
            "Help me prepare for a software engineering interview.",
            "Explain the responsibilities of a Data Analyst."
        ]

        cols = st.columns(2)

        for index, suggestion in enumerate(suggestions):

            with cols[index % 2]:

                if st.button(
                    suggestion,
                    key=f"suggestion_{active_chat_id}_{index}",
                    use_container_width=True
                ):

                    st.session_state.pending_chat_prompt = suggestion
                    st.rerun()

    # DISPLAY OLD MESSAGES

    for message in messages:

        with st.chat_message(message["sender"]):
            st.markdown(message["content"])

    # GET USER INPUT

    prompt = st.session_state.pop(
        "pending_chat_prompt",
        None
    )

    if not prompt:

        prompt = st.chat_input(
            "Ask about jobs, skills, careers or interviews..."
        )

    if prompt:

        prompt = prompt.strip()

        if prompt:

            save_chat_message(
                active_chat_id,
                user_id,
                "user",
                prompt
            )

            if not messages:

                title = prompt[:45].strip()

                if len(prompt) > 45:
                    title += "..."

                update_chat_title(
                    active_chat_id,
                    user_id,
                    title
                )

            updated_messages = get_chat_messages(
                active_chat_id,
                user_id
            )

            conversation_history = [
                {
                    "role": message["sender"],
                    "content": message["content"]
                }
                for message in updated_messages[:-1]
            ]

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):

                with st.spinner("MySpace AI is thinking..."):

                    response = get_ai_response(
                        prompt,
                        conversation_history=conversation_history
                    )

                st.markdown(response)

            save_chat_message(
                active_chat_id,
                user_id,
                "assistant",
                response
            )

            st.rerun()


# =========================================================
# ADMIN AREA
# =========================================================

if is_admin:

    with st.sidebar:

        st.markdown("## 🚀 MySpace Admin")

        st.write(f"Administrator: {current_user['full_name']}")

        st.caption(current_user["email"])

        st.divider()

        admin_page = st.radio(
            "ADMIN MENU",
            [
                "Dashboard",
                "Job Management",
                "User Management",
                "Daily Analytics",
                "AI Assistant"
            ],
            key="admin_navigation"
        )

        st.divider()

        if st.button("Logout", use_container_width=True):
            logout()

    if admin_page == "Dashboard":

        render_hero(
            "Admin Dashboard 👋",
            "Monitor your jobs, users and platform statistics."
        )

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

    elif admin_page == "Job Management":

        render_hero(
            "Job Management",
            "View and search all collected job listings."
        )

        try:

            with sqlite3.connect(DB_PATH) as conn:

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
                """, conn)

            st.write(f"Total listings: {len(job_df)}")

            job_search = st.text_input(
                "Search jobs",
                placeholder="Search by title or company..."
            )

            if job_search:

                mask = (
                    job_df["job_title"].fillna("").str.contains(
                        job_search,
                        case=False,
                        na=False
                    )
                    |
                    job_df["company"].fillna("").str.contains(
                        job_search,
                        case=False,
                        na=False
                    )
                )

                job_df = job_df[mask]

            st.dataframe(
                job_df,
                use_container_width=True,
                hide_index=True
            )

        except Exception as error:
            st.error(f"Unable to load job listings: {error}")

    elif admin_page == "User Management":

        render_hero(
            "User Management",
            "Manage registered accounts and their platform access."
        )

        users = get_all_users()

        if users:

            users_df = pd.DataFrame(users)

            st.write(f"Registered accounts: {len(users_df)}")

            display_df = users_df.drop(
                columns=["id"],
                errors="ignore"
            )

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader("Manage User Access")

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
                st.info("No regular user accounts to manage.")

        else:
            st.info("No registered users found.")

    elif admin_page == "Daily Analytics":

        render_hero(
            "Daily Analytics",
            "Review the daily job collection activity."
        )

        daily_data = get_daily_job_counts()

        if not daily_data.empty:

            st.subheader("Jobs Added Per Day")

            st.bar_chart(
                daily_data.set_index("job_date")["jobs_added"]
            )

            st.subheader("Collection History")

            st.dataframe(
                daily_data,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No daily job data available.")

    elif admin_page == "AI Assistant":

        render_ai_assistant()

    render_footer()
    st.stop()


# =========================================================
# NORMAL USER SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🚀 MySpace")

    st.write(f"Welcome, {current_user['full_name']}")

    st.caption(current_user["email"])

    st.divider()

    st.caption("JOB SEEKER ACCOUNT")

    user_page = st.radio(
        "NAVIGATION",
        [
            "Find Jobs",
            "AI Assistant"
        ],
        key="user_navigation"
    )

    st.divider()

    if st.button("Logout", use_container_width=True):
        logout()


# =========================================================
# USER AI ASSISTANT
# =========================================================

if user_page == "AI Assistant":

    render_ai_assistant()

    render_footer()

    st.stop()


# =========================================================
# LOAD JOBS
# =========================================================

@st.cache_data(ttl=60)
def load_jobs():

    with sqlite3.connect(DB_PATH) as conn:

        df = pd.read_sql_query("""
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
        """, conn)

    return df


def clean_job_description(description):

    if pd.isna(description):
        return "Job description is not available."

    description = html.unescape(str(description))

    soup = BeautifulSoup(description, "html.parser")

    for tag in soup.find_all("br"):
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


# =========================================================
# CITY NORMALIZATION
# =========================================================

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
        "bangalore",
        "bengaluru",
        "banglore"
    ]):
        return "Bangalore"

    if "mumbai" in loc:
        return "Mumbai"

    if "pune" in loc:
        return "Pune"

    if "delhi" in loc:
        return "Delhi"

    if "kolkata" in loc or "calcutta" in loc:
        return "Kolkata"

    if "gurugram" in loc or "gurgaon" in loc:
        return "Gurugram"

    return None


# =========================================================
# USER JOB PAGE
# =========================================================

render_hero(
    "Your Career Starts Here. 🚀",
    "Explore opportunities, discover your potential "
    "and take the first step towards your dream career.",
    [
        "✨ Built for Freshers",
        "💼 Jobs & Internships",
        "🇮🇳 Opportunities Across India"
    ]
)

st.subheader("Find Your Opportunity")

st.caption(
    "Search for jobs that match your interests and preferred location."
)


# =========================================================
# LOAD JOB DATA
# =========================================================

try:

    jobs = load_jobs()

except Exception as error:

    st.error(f"Unable to load jobs: {error}")
    st.stop()


if jobs.empty:

    st.info("No opportunities available right now.")

    render_footer()

    st.stop()


jobs["city"] = jobs["location"].apply(normalize_city)


# =========================================================
# SEARCH AND FILTERS
# =========================================================

search = st.text_input(
    "Search jobs",
    placeholder="🔍 Search by job title or company..."
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
        if str(item).strip().lower() != "unclear"
    ]

    selected_type = st.selectbox(
        "💼 Opportunity Type",
        ["All Types"] + job_types
    )


# =========================================================
# APPLY FILTERS
# =========================================================

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


# =========================================================
# DISPLAY JOBS
# =========================================================

st.divider()

# Job count is intentionally hidden from normal users.

if filtered_jobs.empty:

    st.info(
        "No matching opportunities found. "
        "Try changing your search or filters."
    )

else:

    for _, job in filtered_jobs.iterrows():

        with st.container(border=True):

            title = (
                str(job["job_title"])
                if pd.notna(job["job_title"])
                else "Untitled Position"
            )

            company = (
                str(job["company"])
                if pd.notna(job["company"])
                else "Company not specified"
            )

            st.markdown(
                f'<div class="job-title">{html.escape(title)}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="job-company">🏢 '
                f'{html.escape(company)}</div>',
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

            level = (
                str(job["experience_level"])
                if pd.notna(job["experience_level"])
                else "Not specified"
            )

            st.markdown(
                f'<span class="job-tag">📍 '
                f'{html.escape(str(city))}</span>'
                f'<span class="job-tag">💼 '
                f'{html.escape(level)}</span>'
                f'<span class="job-tag">⏳ '
                f'{html.escape(experience)}</span>',
                unsafe_allow_html=True
            )

            if job["classification_source"] in ["Python", "Groq"]:

                st.success("Experience classified")

            else:

                st.warning(
                    "Shortlisted – eligibility review pending"
                )

            with st.expander("View job description"):

                description = job["job_description"]

                if pd.notna(description) and str(description).strip():

                    st.text(
                        clean_job_description(description)
                    )

                else:

                    st.info(
                        "Job description is not available."
                    )

            if pd.notna(job["job_url"]) and str(job["job_url"]).strip():

                st.link_button(
                    "Apply Now ↗",
                    str(job["job_url"])
                )


# =========================================================
# FOOTER
# =========================================================

render_footer()
