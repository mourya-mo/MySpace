
import re
import html

from bs4 import BeautifulSoup
from src.database import get_connection


# --------------------------------------------------
# 1. CLEAN JOB DESCRIPTION
# --------------------------------------------------

def clean_description(description):

    if not description:
        return ""

    description = html.unescape(description)
    soup = BeautifulSoup(description, "html.parser")

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# --------------------------------------------------
# 2. EXTRACT EXPERIENCE REQUIREMENTS
# --------------------------------------------------

def extract_experience(text):

    text = (text or "").lower()

    text = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
    )

    # Preserve decimal values such as 0.5 years
    sentences = re.split(
        r"(?<=[!?])\s+|(?<=\.)\s+|[\n;]+",
        text
    )

    relevant_sentences = []

    context_pattern = (
        r"\b(experience|experienced|candidate|applicant|"
        r"qualification|qualifications|required|requirement|"
        r"professional|minimum)\b"
    )

    irrelevant_pattern = (
        r"\b(company|organization|business|operating|"
        r"founded|clients|customers)\b"
    )

    for sentence in sentences:

        if not re.search(r"\d", sentence):
            continue

        if re.search(irrelevant_pattern, sentence):
            continue

        if re.search(context_pattern, sentence):
            relevant_sentences.append(sentence)

    if not relevant_sentences:
        return {
            "min_years": None,
            "max_years": None,
            "status": "Unclear"
        }

    relevant_text = " ".join(relevant_sentences)

    # Explicitly no experience required
    no_experience_pattern = (
        r"no experience required|without prior experience|"
        r"no prior experience|zero experience"
    )

    if re.search(no_experience_pattern, relevant_text):
        return {
            "min_years": 0,
            "max_years": 0,
            "status": "Fresher"
        }

    year_unit = r"(?:years?|yrs?|yr)"

    # Example: 2-5 years
    range_pattern = (
        rf"(\d+(?:\.\d+)?)\s*(?:to|-)\s*"
        rf"(\d+(?:\.\d+)?)\s*{year_unit}"
    )

    range_matches = re.findall(range_pattern, relevant_text)

    if range_matches:

        ranges = {
            (float(low), float(high))
            for low, high in range_matches
        }

        if len(ranges) > 1:
            return {
                "min_years": None,
                "max_years": None,
                "status": "Unclear"
            }

        minimum, maximum = next(iter(ranges))

        return {
            "min_years": minimum,
            "max_years": maximum,
            "status": "Range"
        }

    # Example: 5+ years
    minimum_pattern = (
        rf"(\d+(?:\.\d+)?)\s*\+\s*{year_unit}"
    )

    minimum_matches = re.findall(
        minimum_pattern,
        relevant_text
    )

    if minimum_matches:

        values = {float(value) for value in minimum_matches}

        if len(values) > 1:
            return {
                "min_years": None,
                "max_years": None,
                "status": "Unclear"
            }

        return {
            "min_years": next(iter(values)),
            "max_years": None,
            "status": "Minimum"
        }

    # Example: 3 years
    simple_pattern = (
        rf"(\d+(?:\.\d+)?)\s*{year_unit}"
    )

    simple_matches = re.findall(
        simple_pattern,
        relevant_text
    )

    if simple_matches:

        values = {float(value) for value in simple_matches}

        if len(values) > 1:
            return {
                "min_years": None,
                "max_years": None,
                "status": "Unclear"
            }

        years = next(iter(values))

        return {
            "min_years": years,
            "max_years": years,
            "status": "Exact"
        }

    return {
        "min_years": None,
        "max_years": None,
        "status": "Unclear"
    }


# --------------------------------------------------
# 3. CLASSIFY EXPERIENCE LEVEL
# --------------------------------------------------

def classify_experience(title, description):

    title_lower = (title or "").lower()
    text = (description or "").lower()

    # Internship detection
    if re.search(r"\b(intern|internship)\b", title_lower):
        return "Internship"

    experience = extract_experience(text)
    minimum = experience["min_years"]

    # Explicit experience requirement takes priority
    if minimum is not None:

        if minimum >= 2:
            return "Experienced"

        if minimum == 0:
            return "Fresher"

        return "Unclear"

    # Strong seniority indicators
    senior_keywords = [
        "senior",
        "staff engineer",
        "principal",
        "lead engineer",
        "engineering manager",
        "director",
        "vice president",
        "architect"
    ]

    if any(keyword in title_lower for keyword in senior_keywords):
        return "Experienced"

    # Explicit fresher-friendly indicators
    fresher_keywords = [
        "fresh graduates",
        "recent graduates",
        "entry-level position",
        "entry level position",
        "no experience required",
        "without prior experience",
        "freshers can apply"
    ]

    if any(keyword in text for keyword in fresher_keywords):
        return "Fresher"

    return "Unclear"


# --------------------------------------------------
# 4. PROCESS AND SAVE PYTHON CLASSIFICATIONS
# --------------------------------------------------

def process_python_classification():

    connection = get_connection()

    counts = {
        "Fresher": 0,
        "Internship": 0,
        "Experienced": 0,
        "Unclear": 0
    }

    try:

        jobs = connection.execute("""
            SELECT
                id,
                job_title,
                job_description
            FROM jobs
            WHERE LOWER(location) LIKE '%india%'
            AND experience_level IS NULL
            ORDER BY id
        """).fetchall()

        print("\nTotal jobs to process:", len(jobs))

        for job in jobs:

            description = clean_description(
                job["job_description"]
            )

            classification = classify_experience(
                job["job_title"],
                description
            )

            counts[classification] += 1

            if classification == "Unclear":
                continue

            connection.execute("""
                UPDATE jobs
                SET experience_level = ?,
                    classification_source = ?
                WHERE id = ?
                AND experience_level IS NULL
            """, (
                classification,
                "Python",
                job["id"]
            ))

        connection.commit()

        print("\n========== PYTHON CLASSIFICATION SUMMARY ==========")

        for category, count in counts.items():
            print(f"{category}: {count}")

        print("\nPython classifications saved successfully.")
        print("Unclear jobs left for Groq:", counts["Unclear"])

    except Exception:

        connection.rollback()
        raise

    finally:
        connection.close()


# --------------------------------------------------
# 5. EXECUTION
# --------------------------------------------------

if __name__ == "__main__":
    process_python_classification()
