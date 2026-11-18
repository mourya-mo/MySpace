
import re
from database import get_connection

def get_india_jobs():
    connection = get_connection()

    query = """
        SELECT *
        FROM jobs
        WHERE
            LOWER(location) LIKE '%india%'
            OR LOWER(location) LIKE '%bangalore%'
            OR LOWER(location) LIKE '%bengaluru%'
            OR LOWER(location) LIKE '%mumbai%'
            OR LOWER(location) LIKE '%pune%'
            OR LOWER(location) LIKE '%hyderabad%'
            OR LOWER(location) LIKE '%chennai%'
            OR LOWER(location) LIKE '%delhi%'
    """

    jobs = connection.execute(query).fetchall()
    connection.close()

    return jobs


def filter_entry_level_jobs(jobs):

    keywords = [
        "intern",
        "internship",
        "fresher",
        "entry level",
        "entry-level",
        "graduate",
        "trainee",
        "junior",
        "associate"
    ]

    filtered_jobs = []

    for job in jobs:
        title = (job["job_title"] or "").lower()

        if any(keyword in title for keyword in keywords):
            filtered_jobs.append(job)

    return filtered_jobs


def extract_experience(job):

    text = (
        (job["job_title"] or "") + " " +
        (job["job_description"] or "")
    ).lower()

    patterns = [
        r"(\d+)\+?\s+years? of relevant experience",
        r"(\d+)\+?\s+years? of professional experience",
        r"minimum of (\d+)\+?\s+years? of experience",
        r"at least (\d+)\+?\s+years? of experience"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return int(match.group(1))

    return None


if __name__ == "__main__":

    india_jobs = get_india_jobs()
    entry_jobs = filter_entry_level_jobs(india_jobs)

    print("Total India jobs:", len(india_jobs))
    print("Potential fresher/internship jobs:", len(entry_jobs))

    print("\nExperience requirement check:")

    for job in entry_jobs[:20]:

        years = extract_experience(job)

        experience = (
            f"{years} years"
            if years is not None
            else "Not identified"
        )

        print(
            job["job_title"],
            "|",
            experience
        )
