import requests
from src.database import save_jobs

def fetch_greenhouse_jobs(board_token, company_name):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(f"Failed to fetch jobs from {company_name}")
        return []

    data = response.json()
    jobs = []

    for job in data.get("jobs", []):
        job_data = {
            "job_title": job.get("title"),
            "company": company_name,
            "location": job.get("location", {}).get("name"),
            "job_description": job.get("content"),
            "job_url": job.get("absolute_url"),
            "source": "Greenhouse"
        }

        jobs.append(job_data)

    return jobs


if __name__ == "__main__":
    jobs = fetch_greenhouse_jobs("greenhouse", "Greenhouse")
    print("Total jobs colled:",len(jobs))
    saved=save_jobs(jobs)
    print("New jobs saved :",saved)