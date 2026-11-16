
import requests


GREENHOUSE_COMPANIES = [
    ("gitlab", "GitLab"),
    ("figma", "Figma"),
    ("discord", "Discord"),
    ("stripe", "Stripe"),
    ("airbnb", "Airbnb")
]


INDIA_LOCATIONS = [
    "india",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "pune",
    "mumbai",
    "chennai",
    "gurgaon",
    "gurugram",
    "noida",
    "delhi",
    "kolkata"
]


def is_india_job(location):
    """Check whether a job location matches an Indian location."""

    location = (location or "").lower()

    return any(city in location for city in INDIA_LOCATIONS)


def test_greenhouse_boards():

    print("\n========== GREENHOUSE JOB BOARD TESTING ==========")

    total_jobs = 0
    total_india_jobs = 0

    for board_token, company_name in GREENHOUSE_COMPANIES:

        url = (
            f"https://boards-api.greenhouse.io/v1/boards/"
            f"{board_token}/jobs"
        )

        try:
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                print(f"\n{company_name}: Board unavailable")
                print("Status:", response.status_code)
                continue

            jobs = response.json().get("jobs", [])

            india_jobs = [
                job for job in jobs
                if is_india_job(
                    job.get("location", {}).get("name")
                )
            ]

            total_jobs += len(jobs)
            total_india_jobs += len(india_jobs)

            print("\n" + "=" * 65)
            print(f"COMPANY: {company_name}")
            print(f"TOTAL JOBS: {len(jobs)}")
            print(f"INDIA JOBS: {len(india_jobs)}")
            print("=" * 65)

            for index, job in enumerate(india_jobs, start=1):

                print(f"\n{index}. Company: {company_name}")
                print(f"   Job Title: {job.get('title')}")
                print(
                    "   Location:",
                    job.get("location", {}).get("name")
                )
                print(
                    "   Application URL:",
                    job.get("absolute_url")
                )

        except requests.RequestException as error:
            print(f"\n{company_name}: Request failed - {error}")

    print("\n" + "=" * 65)
    print("FINAL SUMMARY")
    print("=" * 65)
    print("Total jobs across boards:", total_jobs)
    print("Total India-based jobs:", total_india_jobs)


if __name__ == "__main__":
    test_greenhouse_boards()
