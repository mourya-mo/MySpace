
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

    sentences = re.split(r"[;!\n?]+|(?<=\.)\s+", text)

    context_pattern = (
        r"\b(experience|experienced|candidate|applicant|"
        r"qualification|required|requirement|professional|"
        r"minimum|work experience)\b"
    )

    relevant_sentences = [
        sentence for sentence in sentences
        if re.search(r"\d", sentence)
        and re.search(context_pattern, sentence)
    ]

    relevant_text = " ".join(relevant_sentences)

    if not relevant_text:
        return {
            "min_years": None,
            "max_years": None,
            "status": "Unclear"
        }

    # Explicitly no experience required.
    no_experience_pattern = (
        r"\bno experience required\b|"
        r"\bno prior experience\b|"
        r"\bwithout prior experience\b|"
        r"\bzero experience\b"
    )

    if re.search(no_experience_pattern, text):

        return {
            "min_years": 0,
            "max_years": 0,
            "status": "Fresher"
        }

    # Example: 0-2 years or 1 to 2 years.
    range_pattern = (
        rf"\b(\d+(?:\.\d+)?)\s*(?:to|-)\s*"
        rf"(\d+(?:\.\d+)?)\s*{year_unit}\b"
    )

    range_matches = re.findall(range_pattern, relevant_text)

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

    # Example: 2+ years, at least 2 years.
    minimum_pattern = (
        rf"\b(\d+(?:\.\d+)?)\s*\+\s*{year_unit}\b|"
        rf"\bat least\s+(\d+(?:\.\d+)?)\s*{year_unit}\b|"
        rf"\bminimum of\s+(\d+(?:\.\d+)?)\s*{year_unit}\b"
    )

    minimum_matches = re.findall(
        minimum_pattern, relevant_text
    )

    if minimum_matches:

        values = {
            float(next(value for value in match if value))
            for match in minimum_matches
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
        rf"\b(\d+(?:\.\d+)?)\s*{year_unit}\b"
    )

    simple_matches = re.findall(simple_pattern, relevant_text)

    if simple_matches:

        values = {float(value) for value in simple_matches}

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

    senior_patterns = [
        r"\bsenior\b",
        r"\bsr\.?\b",
        r"\bstaff engineer\b",
        r"\bprincipal\b",
        r"\blead engineer\b",
        r"\bteam lead\b",
        r"\btechnical lead\b",
        r"\bengineering manager\b",
        r"\bproduct manager\b",
        r"\bproject manager\b",
        r"\bprogram manager\b",
        r"\bdirector\b",
        r"\bvice president\b",
        r"\bvp\b",
        r"\bhead of\b",
        r"\barchitect\b"
    ]

    return any(
        re.search(pattern, title)
        for pattern in senior_patterns
    )


# --------------------------------------------------
# 4. CLASSIFY FRESHER ELIGIBILITY
# --------------------------------------------------

def classify_experience(title, description):

    title_lower = (title or "").lower()
    text = clean_description(description).lower()

    # Seniority check.
    if is_senior_title(title_lower):
        return "Not eligible"

    experience = extract_experience(text)

    minimum = experience["min_years"]
    maximum = experience["max_years"]
    status = experience["status"]

    # Explicit experience requirements.
    if minimum is not None:

        if maximum is not None:

            if 0 <= minimum <= maximum <= 2:
                return "Eligible"

            return "Not eligible"

        # 2+ or at least 2 years exceeds the strict limit.
        if minimum >= 2:
            return "Not eligible"

        # 0+ or 1+ is not sufficiently precise.
        return "Unclear"

    # Internship positions.
    if re.search(r"\b(intern|internship)\b", title_lower):
        return "Eligible"

    # Explicit fresher-friendly indicators.
    fresher_patterns = [
        r"\bfreshers?\b",
        r"\bfresh graduates?\b",
        r"\brecent graduates?\b",
        r"\bnew graduates?\b",
        r"\brecent university graduates?\b",
        r"\bentry[- ]level position\b",
        r"\bno experience required\b",
        r"\bwithout prior experience\b",
        r"\ngraduate trainee\b",
        r"\bcampus hiring\b",
        r"\bcampus recruitment\b",
        r"\buniversity graduate program\b",
        r"\bgraduate program\b",
        r"\bgraduate programme\b"
    ]

    if any(re.search(pattern, text) for pattern in fresher_patterns):
        return "Eligible"

    return "Unclear"
