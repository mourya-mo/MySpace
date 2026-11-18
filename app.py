
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="MySpace | Find Your Next Opportunity",
    page_icon="🚀",
    layout="wide"
)

DB_PATH = Path(__file__).parent / "data" / "fresher_jobs.db"


# ---------------- CUSTOM STYLING ----------------

st.markdown("""
<style>
    .stApp {
        background-color: #0b1120;
        color: #f1f5f9;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1150px;
    }

    h1 {
        color: #ffffff;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }

    h2, h3 {
        color: #f8fafc !important;
    }

    .hero-text {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: -12px;
        margin-bottom: 25px;
    }

    .section-label {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    div[data-testid="stTextInput"] input {
        background-color: #172238;
        color: white;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #172238;
        border-color: #334155;
        border-radius: 10px;
        color: white;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #111c30;
        border: 1px solid #26364f;
        border-radius: 14px;
        padding: 10px;
    }

    .job-company {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 12px;
    }

    .job-tag {
        display: inline-block;
        background-color: #1e3a5f;
        color: #93c5fd;
        padding: 5px 11px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin-right: 7px;
        margin-bottom: 8px;
    }

    .stLinkButton a {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }

    hr {
        border-color: #26364f;
    }

    [data-testid="stCaptionContainer"] {
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)


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
            created_at
        FROM fresher_jobs
        ORDER BY id DESC
        """,
        conn
    )

    conn.close()
    return df


# ---------------- LOCATION CLEANING ----------------

def get_city(location):
    if pd.isna(location) or not str(location).strip():
        return "Not specified"

    parts = [part.strip() for part in str(location).split(",")]
    return parts[0] if parts else "Not specified"


# ---------------- HEADER ----------------

st.markdown("# 🚀 MySpace")
st.markdown(
    '<p class="hero-text">Discover opportunities. Build your future. '
    'Find the right start to your career.</p>',
    unsafe_allow_html=True
)

st.divider()


# ---------------- LOAD JOBS ----------------

try:
    jobs = load_jobs()
except Exception as e:
    st.error(f"Unable to load jobs: {e}")
    st.stop()

if jobs.empty:
    st.warning("No jobs are currently available.")
    st.stop()

# Hide unclear classifications
jobs = jobs[
    jobs["experience_level"].fillna("").str.strip().str.lower() != "unclear"
].copy()

# Create a city column for filtering
jobs["city"] = jobs["location"].apply(get_city)


# ---------------- SEARCH AND FILTERS ----------------

st.markdown("### Find your next opportunity")

search = st.text_input(
    "Search jobs",
    placeholder="🔍  Search by job title or company..."
)

col1, col2 = st.columns(2)

with col1:
    cities = sorted(
        city for city in jobs["city"].unique()
        if city != "Not specified"
    )

    selected_city = st.selectbox(
        "📍 City",
        ["All Cities"] + cities
    )

with col2:
    job_types = sorted(
        jobs["experience_level"].dropna().unique().tolist()
    )

    job_types = [
        job_type for job_type in job_types
        if job_type.strip().lower() != "unclear"
    ]

    selected_type = st.selectbox(
        "💼 Opportunity Type",
        ["All Types"] + job_types
    )


# ---------------- FILTER LOGIC ----------------

filtered_jobs = jobs.copy()

if search:
    search_mask = (
        filtered_jobs["job_title"].fillna("").str.contains(
            search, case=False, na=False
        )
        |
        filtered_jobs["company"].fillna("").str.contains(
            search, case=False, na=False
        )
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


# ---------------- JOB RESULTS ----------------

st.divider()

st.markdown(
    f"### Opportunities <span style='color:#60a5fa;'>({len(filtered_jobs)})</span>",
    unsafe_allow_html=True
)

if filtered_jobs.empty:
    st.info("No matching opportunities found. Try changing your search or filters.")

else:
    for _, job in filtered_jobs.iterrows():

        with st.container(border=True):

            st.markdown(f"### {job['job_title']}")

            st.markdown(
                f'<div class="job-company">🏢 {job["company"]}</div>',
                unsafe_allow_html=True
            )

            min_exp = job["min_experience"]
            max_exp = job["max_experience"]

            if pd.notna(min_exp) and pd.notna(max_exp):
                experience = f"{min_exp:g}–{max_exp:g} years"
            elif pd.notna(min_exp):
                experience = f"{min_exp:g}+ years"
            else:
                experience = "Not specified"

            st.markdown(
                f"""
                <span class="job-tag">📍 {job['city']}</span>
                <span class="job-tag">💼 {job['experience_level'] or 'Not specified'}</span>
                <span class="job-tag">⏳ {experience}</span>
                """,
                unsafe_allow_html=True
            )

            with st.expander("View job details"):
                description = job["job_description"]

                if pd.notna(description) and str(description).strip():
                    st.write(description)
                else:
                    st.info("No job description available.")

            if pd.notna(job["job_url"]) and str(job["job_url"]).strip():
                st.link_button("Apply Now ↗", str(job["job_url"]))


# ---------------- FOOTER ----------------

st.divider()

st.markdown(
    "<p style='text-align:center;color:#64748b;'>"
    "MySpace · Your career starts here 🚀"
    "</p>",
    unsafe_allow_html=True
)
