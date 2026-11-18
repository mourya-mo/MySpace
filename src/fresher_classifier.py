
import re
import html
from bs4 import BeautifulSoup


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

    year_unit = r"(?:years?|yrs?|yr)"

    # Find sentences containing experience-related terms.
    sentences = re.split(
        r"(?<=[!?])\s+|(?<=\.)\s+|[;\n]+",
        text
    )

    relevant_sentences = []

    context_pattern = (
        r"\b(experience|experienced|candidate|applicant|"
        r"qualification|qualifications|required|requirement|"
        r"professional|minimum|work experience)\b"
    )

    for sentence in sentences:

        if not re.search(r"\d", sentence):
            continue

        if re.search(context_pattern, sentence):
            relevant_sentences.append(sentence)

    relevant_text = " ".join(relevant_sentences)

    if not relevant_text:
        return {
            "min_years": None,
            "max_years": None,
            "status": "Unclear"
        }

    # Explicitly no experience required.
    no_experience_pattern = (
        r"no experience required|"
        r"no prior experience|"
        r"without prior experience|"
        r"zero experience"
    )

    if re.search(no_experience_pattern, relevant_text):

        return {
            "min_years": 0,
            "max_years": 0,
            "status": "Fresher"
        }

    # Example: 0-2 years or 1 to 2 years.
    range_pattern = (
        rf"(\d+(?:\.\d+)?)\s*(?:to|-)\s*"
        rf"(\d+(?:\.\d+)?)\s*{year_unit}"
    )

    range_matches = re.findall(
        range_pattern,
        relevant_text
    )

    if range_matches:

        ranges = {
            (float(low), float(high))
            for low, high in range_matches
        }

        if len(ranges) != 1:

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

    # Example: 2+ years or at least 2 years.
    minimum_pattern = (
        rf"(?:at least\s+)?(\d+(?:\.\d+)?)\s*\+\s*{year_unit}|"
        rf"at least\s+(\d+(?:\.\d+)?)\s*{year_unit}"
    )

    minimum_matches = re.findall(
        minimum_pattern,
        relevant_text
    )

    if minimum_matches:

        values = {
            float(first or second)
            for first, second in minimum_matches
        }

        if len(values) != 1:

            return {
                "min_years": None,
                "max_years": None,
                "status": "Unclear"
            }

        years = next(iter(values))

        return {
            "min_years": years,
            "max_years": None,
            "status": "Minimum"
        }

    # Example: 1 year of experience.
    simple_pattern = (
        rf"(\d+(?:\.\d+)?)\s*{year_unit}"
    )

    simple_matches = re.findall(
        simple_pattern,
        relevant_text
    )

    if simple_matches:

        values = {
            float(value)
            for value in simple_matches
        }

        if len(values) != 1:

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
# 3. TITLE VALIDATION
# --------------------------------------------------

def is_senior_title(title):

    title = (title or "").lower()

    senior_keywords = [
        "senior",
        "sr.",
        "staff engineer",
        "staff software",
        "principal",
        "lead engineer",
        "team lead",
        "technical lead",
        "engineering manager",
        "product manager",
        "project manager",
        "program manager",
        "director",
        "vice president",
        "vp ",
        "head of",
        "architect"
    ]

    return any(
        keyword in title
        for keyword in senior_keywords
    )


# --------------------------------------------------
# 4. CLASSIFY FRESHER ELIGIBILITY
# --------------------------------------------------

def classify_experience(title, description):

    title_lower = (title or "").lower()

    text = clean_description(description).lower()

    # Seniority check comes first.
    if is_senior_title(title_lower):
        return "Not eligible"

    experience = extract_experience(text)

    minimum = experience["min_years"]
    maximum = experience["max_years"]

    # Explicit experience requirements.
    if minimum is not None:

        # Exact or range: both boundaries must be 0-2.
        if maximum is not None:

            if minimum >= 0 and maximum <= 2:
                return "Eligible"

            return "Not eligible"

        # Minimum-only requirement such as 2+ years.
        if minimum > 2:
            return "Not eligible"

        # 0+, 1+ or 2+ needs further validation.
        return "Unclear"

    # Internship detection.
    if re.search(r"\b(intern|internship)\b", title_lower):
        return "Eligible"

    # Explicit fresher-friendly indicators.
    fresher_keywords = [
        "fresh graduates",
        "recent graduates",
        "entry-level position",
        "entry level position",
        "no experience required",
        "without prior experience",
        "freshers can apply",
        "new graduate",
        "graduate trainee"
    ]

    if any(keyword in text for keyword in fresher_keywords):
        return "Eligible"

    return "Unclear"
