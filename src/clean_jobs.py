
import json
import re
from pathlib import Path
from urllib.parse import urlparse

INPUT_FILE = Path("data/tavily_jobs.json")
OUTPUT_FILE = Path("data/cleaned_tavily_jobs.json")

JOB_KEYWORDS = [
    "software engineer",
    "software developer",
    "python developer",
    "java developer",
    "data analyst",
    "data scientist",
    "machine learning",
    "artificial intelligence",
    "ai engineer",
    "business analyst",
    "cloud engineer",
    "devops engineer",
    "cybersecurity",
    "intern",
    "internship",
    "graduate trainee",
    "graduate engineer",
    "product analyst"
]

INDIA_KEYWORDS = [
    "india",
    "bengaluru",
    "bangalore",
    "hyderabad",
    "pune",
    "mumbai",
    "chennai",
    "delhi"
]

PORTAL_DOMAINS = [
    "elitmus.com",
    "wellfound.com",
    "indeed.com",
    "naukri.com",
    "linkedin.com"
]

EXPIRED_KEYWORDS = [
    "expired",
    "position has been filled",
    "no longer accepting applications"
]


def clean_text(text):
    """Remove HTML tags and normalize text."""

    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_relevant_job(job):

    title = clean_text(job.get("job_title", "")).lower()
    description = clean_text(
        job.get("job_description", "")
    ).lower()

    combined_text = title + " " + description

    if not any(keyword in combined_text for keyword in JOB_KEYWORDS):
        return False

    if not any(keyword in combined_text for keyword in INDIA_KEYWORDS):
        return False

    if any(keyword in combined_text for keyword in EXPIRED_KEYWORDS):
        return False

    return True


def clean_jobs(jobs):

    unique_jobs = {}
    rejected_count = 0

    for job in jobs:

        url = job.get("job_url", "").strip()
        parsed_url = urlparse(url)

        if parsed_url.scheme != "https" or not parsed_url.netloc:
            rejected_count += 1
            continue

        if not is_relevant_job(job):
            rejected_count += 1
            continue

        normalized_url = url.split("?")[0].rstrip("/").lower()

        if normalized_url not in unique_jobs:
            job["job_title"] = clean_text(job.get("job_title", ""))
            job["job_description"] = clean_text(
                job.get("job_description", "")
            )

            unique_jobs[normalized_url] = job

    return list(unique_jobs.values()), rejected_count


if __name__ == "__main__":

    with open(INPUT_FILE, "r") as file:
        jobs = json.load(file)

    cleaned_jobs, rejected = clean_jobs(jobs)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w") as file:
        json.dump(cleaned_jobs, file, indent=4)

    print("Original results:", len(jobs))
    print("Rejected results:", rejected)
    print("Unique relevant results:", len(cleaned_jobs))
    print("Saved to:", OUTPUT_FILE)
