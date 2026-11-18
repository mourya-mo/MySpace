
import json
import requests

from pathlib import Path

from src.fresher_classifier import (
    clean_description,
    extract_experience,
    classify_experience
)

from src.fresher_database import (
    create_fresher_tables,
    save_fresher_jobs
)


BOARDS_FILE = Path("data/job_boards.json")


# --------------------------------------------------
# INDIA LOCATION FILTER
# --------------------------------------------------

INDIA_LOCATIONS = [
    "india",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "chennai",
    "mumbai",
    "pune",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "kolkata",
    "kochi",
    "coimbatore",
    "ahmedabad",
    "jaipur"
]


def is_india_job(location, description):
    location = (location or "").lower()
    description = (description or "").lower()

    # Explicit India or Indian city in job location.
    if any(place in location for place in INDIA_LOCATIONS):
        return True

    # Remote jobs are included only when India eligibility
    # is explicitly mentioned in their description.
    if "remote" in location:
        india_phrases = [
            "remote - india",
            "remote, india",
            "based in india",
            "located in india",
            "india only",
            "within india"
        ]

        if any(phrase in description for phrase in india_phrases):
            return True

    return False


# --------------------------------------------------
# STANDARD JOB FORMAT
# --------------------------------------------------

def make_job(title, company, location, description, url, source):

    if not title or not url:
        return None

    return {
        "job_title": title.strip(),
        "company": company,
        "location": location or "Not specified",
        "job_description": description or "",
        "job_url": url,
        "source": source
    }


# --------------------------------------------------
# GREENHOUSE
# --------------------------------------------------

def fetch_greenhouse_jobs(board_id, company):

    url = (
        f"https://boards-api.greenhouse.io/v1/boards/"
        f"{board_id}/jobs?content=true"
    )

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError) as error:
        print(f"Greenhouse failed - {company}: {error}")
        return []

    jobs = []

    for job in data.get("jobs", []):

        location_data = job.get("location") or {}

        job_data = make_job(
            title=job.get("title"),
            company=company,
            location=location_data.get("name"),
            description=job.get("content"),
            url=job.get("absolute_url"),
            source="Greenhouse"
        )

        if job_data:
            jobs.append(job_data)

    return jobs


# --------------------------------------------------
# LEVER
# --------------------------------------------------

def fetch_lever_jobs(board_id, company):

    url = f"https://api.lever.co/v0/postings/{board_id}?mode=json"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError) as error:
        print(f"Lever failed - {company}: {error}")
        return []

    jobs = []

    for job in data:

        categories = job.get("categories") or {}

        location = (
            categories.get("location")
            or ", ".join(categories.get("allLocations") or [])
        )

        description = (
            job.get("descriptionPlain")
            or job.get("description")
            or ""
        )

        job_data = make_job(
            title=job.get("text"),
            company=company,
            location=location,
            description=description,
            url=job.get("hostedUrl") or job.get("applyUrl"),
            source="Lever"
        )

        if job_data:
            jobs.append(job_data)

    return jobs


# --------------------------------------------------
# ASHBY
# --------------------------------------------------

def fetch_ashby_jobs(board_id, company):

    url = (
        f"https://api.ashbyhq.com/posting-api/job-board/"
        f"{board_id}"
    )

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError) as error:
        print(f"Ashby failed - {company}: {error}")
        return []

    jobs = []

    for job in data.get("jobs", []):

        if job.get("isListed") is False:
            continue

        address = job.get("address") or {}
        postal_address = address.get("postalAddress") or {}

        location = (
            job.get("location")
            or postal_address.get("addressLocality")
        )

        description = (
            job.get("descriptionPlain")
            or job.get("descriptionHtml")
            or ""
        )

        job_data = make_job(
            title=job.get("title"),
            company=company,
            location=location,
            description=description,
            url=job.get("jobUrl") or job.get("applyUrl"),
            source="Ashby"
        )

        if job_data:
            jobs.append(job_data)

    return jobs


# --------------------------------------------------
# LOAD COMPANY BOARDS
# --------------------------------------------------

def load_job_boards():

    if not BOARDS_FILE.exists():
        raise FileNotFoundError(
            "job_boards.json not found. Run discovery first."
        )

    with open(BOARDS_FILE, "r") as file:
        return json.load(file)


# --------------------------------------------------
# FILTER INDIA + FRESHER JOBS
# --------------------------------------------------

def filter_fresher_jobs(all_jobs):

    india_count = 0
    eligible_count = 0
    excluded_count = 0
    unclear_count = 0

    fresher_jobs = []

    for job in all_jobs:

        description = clean_description(
            job["job_description"]
        )

        # First: India filter.
        if not is_india_job(job["location"], description):
            continue

        india_count += 1

        # Second: experience classification.
        result = classify_experience(
            job["job_title"],
            description
        )

        if result == "Not eligible":
            excluded_count += 1
            continue

        if result == "Unclear":
            unclear_count += 1
            continue

        experience = extract_experience(description)

        # Keep only validated eligible jobs.
        job["experience_level"] = (
            "Internship"
            if result == "Eligible"
            and "intern" in job["job_title"].lower()
            else "Fresher"
        )

        job["min_experience"] = experience["min_years"]
        job["max_experience"] = experience["max_years"]
        job["classification_source"] = "Python"

        fresher_jobs.append(job)
        eligible_count += 1

    print("\n========== FILTER SUMMARY ==========")
    print("India-based jobs:", india_count)
    print("Eligible fresher jobs:", eligible_count)
    print("Experienced jobs excluded:", excluded_count)
    print("Unclear jobs pending validation:", unclear_count)

    return fresher_jobs


# --------------------------------------------------
# COLLECT ALL JOBS
# --------------------------------------------------

def collect_all_jobs():

    boards = load_job_boards()
    all_jobs = []

    print("Total discovered boards:", len(boards))

    collectors = {
        "greenhouse": fetch_greenhouse_jobs,
        "lever": fetch_lever_jobs,
        "ashby": fetch_ashby_jobs
    }

    for board in boards:

        platform = board.get("platform", "").lower()
        board_id = board.get("board_id")
        company = board.get("company", board_id)

        collector = collectors.get(platform)

        if not collector or not board_id:
            continue

        print(f"\nFetching {platform} jobs from {company}...")

        jobs = collector(board_id, company)

        print("Jobs fetched:", len(jobs))

        all_jobs.extend(jobs)

    return all_jobs


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    # Create the separate fresher database table.
    create_fresher_tables()

    # Collect postings from all discovered boards.
    all_jobs = collect_all_jobs()

    print("\nTotal jobs collected:", len(all_jobs))

    # Filter India-based and eligible jobs.
    fresher_jobs = filter_fresher_jobs(all_jobs)

    # Save only eligible jobs in the new database.
    saved = save_fresher_jobs(fresher_jobs)

    print("\n========== FINAL SUMMARY ==========")
    print("Total jobs fetched:", len(all_jobs))
    print("Eligible jobs identified:", len(fresher_jobs))
    print("New fresher jobs saved:", saved)
    print("Database: data/fresher_jobs.db")
