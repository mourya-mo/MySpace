
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="MySpace | Discover Your Future",
    page_icon="🚀",
    layout="wide"
)

DB_PATH = Path(__file__).parent / "data" / "fresher_jobs.db"


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


# Remove unclear opportunities
jobs = jobs[
    jobs["experience_level"]
    .fillna("")
    .str.strip()
    .str.lower() != "unclear"
].copy()

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

            with st.expander("View job description"):

                description = job["job_description"]

                if pd.notna(description) and str(description).strip():
                    st.write(description)

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
