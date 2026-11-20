
import os
import json
import argparse

from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from dotenv import load_dotenv
from tavily import TavilyClient


# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv()

API_KEY = os.getenv("TAVILY_API_KEY")

if not API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from .env")

client = TavilyClient(api_key=API_KEY)

# Separate storage: no connection to existing ATS files.
JOBS_FILE = Path("data/company_portal_jobs.json")
SEEN_URLS_FILE = Path("data/company_portal_seen_urls.json")


# ==================================================
# REPUTED COMPANIES AND OFFICIAL DOMAINS
# ==================================================

COMPANIES = {
    "Google": ["google.com", "careers.google.com"],
    "Microsoft": ["careers.microsoft.com"],
    "Amazon": ["amazon.jobs"],
    "Adobe": ["adobe.com", "careers.adobe.com"],
    "Oracle": ["oracle.com", "careers.oracle.com"],
    "IBM": ["ibm.com", "careers.ibm.com"],
    "Cisco": ["cisco.com", "jobs.cisco.com"],
    "Intel": ["intel.com", "jobs.intel.com"],
    "Qualcomm": ["qualcomm.com", "careers.qualcomm.com"],
    "SAP": ["sap.com", "jobs.sap.com"],
    "Accenture": ["accenture.com"],
    "Deloitte": ["deloitte.com"],
    "Capgemini": ["capgemini.com"],
    "TCS": ["tcs.com"],
    "Infosys": ["infosys.com"],
    "JPMorgan Chase": ["jpmorganchase.com"],
    "Salesforce": ["salesforce.com"],
    "NVIDIA": ["nvidia.com"],
    "PayPal": ["paypal.com"],
    "Walmart Global Tech": ["walmart.com"],
    "Uber": ["uber.com"],
    "Flipkart": ["flipkart.com"]
}


# ==================================================
# SEARCH CONFIGURATION
# ==================================================

MAX_RESULTS_PER_COMPANY = 10

SEARCH_TERMS = [
    "fresher graduate hiring India",
    "software engineer internship India",
    "entry level developer jobs India",
    "graduate trainee technology jobs India",
    "data analyst internship graduate jobs India"
]

ROLE_KEYWORDS = [
    "intern",
    "internship",
    "graduate",
    "fresher",
    "trainee",
    "entry level",
    "new grad",
    "associate",
    "junior",
    "software engineer",
    "developer",
    "data analyst",
    "technology analyst",
    "apprentice"
]


# ==================================================
# URL NORMALISATION
# ==================================================

def normalize_url(url):

    try:
        parsed = urlparse(url.strip())

        if parsed.scheme not in ("http", "https"):
            return None

        tracking_parameters = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "gclid",
            "fbclid"
        }

        query = [
            (key, value)
            for key, value in parse_qsl(parsed.query)
            if key.lower() not in tracking_parameters
        ]

        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            urlencode(query),
            ""
        ))

    except Exception:
        return None


# ==================================================
# OFFICIAL DOMAIN VALIDATION
# ==================================================

def is_official_company_url(url, domains):

    host = urlparse(url).netloc.lower().split(":")[0]

    return any(
        host == domain or host.endswith("." + domain)
        for domain in domains
    )


# ==================================================
# JOB RELEVANCE CHECK
# ==================================================

def looks_like_job(title, description):

    text = f"{title} {description}".lower()

    return any(
        keyword in text
        for keyword in ROLE_KEYWORDS
    )


# ==================================================
# LOAD EXISTING DATA
# ==================================================

def load_json(file_path, default):

    if not file_path.exists():
        return default

    try:
        with open(file_path, "r") as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError):
        print(f"Warning: Could not read {file_path}")
        return default


def load_existing_jobs():

    data = load_json(JOBS_FILE, [])

    return data if isinstance(data, list) else []


def load_seen_urls():

    data = load_json(SEEN_URLS_FILE, [])

    if not isinstance(data, list):
        data = []

    return set(data)


# ==================================================
# SAVE DATA SAFELY
# ==================================================

def save_json(file_path, data):

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_file = file_path.with_suffix(".tmp")

    with open(temporary_file, "w") as file:
        json.dump(data, file, indent=4)

    temporary_file.replace(file_path)


def save_new_jobs(new_jobs, seen_urls):

    existing_jobs = load_existing_jobs()

    unique_jobs = {}

    # Preserve all previous job records.
    for job in existing_jobs:

        url = normalize_url(job.get("job_url", ""))

        if url:
            unique_jobs[url] = job
            seen_urls.add(url)

    inserted = 0

    for job in new_jobs:

        url = normalize_url(job.get("job_url", ""))

        if not url or url in unique_jobs:
            continue

        unique_jobs[url] = job
        seen_urls.add(url)
        inserted += 1

    # Save job records first, then the seen URL registry.
    save_json(
        JOBS_FILE,
        list(unique_jobs.values())
    )

    save_json(
        SEEN_URLS_FILE,
        sorted(seen_urls)
    )

    return inserted, len(unique_jobs)


# ==================================================
# TAVILY COMPANY JOB DISCOVERY
# ==================================================

def discover_company_jobs(company, domains, seen_urls):

    discovered = []

    for search_term in SEARCH_TERMS:

        query = (
            f"{company} India {search_term} "
            "official careers job openings"
        )

        print(f"\nSearching: {company} | {search_term}")

        try:

            response = client.search(
                query=query,
                search_depth="basic",
                max_results=MAX_RESULTS_PER_COMPANY,
                include_domains=domains
            )

            results = response.get("results", [])

            print("Search results:", len(results))

            for result in results:

                original_url = result.get("url", "").strip()

                if not original_url:
                    continue

                url = normalize_url(original_url)

                if not url:
                    continue

                # Only accept official company domains.
                if not is_official_company_url(url, domains):
                    continue

                # Skip previously discovered links.
                if url in seen_urls:
                    continue

                title = result.get("title", "").strip()
                description = result.get("content", "").strip()

                # Avoid storing unrelated company pages.
                if not looks_like_job(title, description):
                    continue

                discovered.append({
                    "company": company,
                    "job_title": title,
                    "job_url": url,
                    "description_snippet": description,
                    "source": "Tavily",
                    "search_query": query,
                    "published_date": result.get("published_date"),
                    "location": "India - Pending Verification",
                    "experience_level": "Pending Verification",
                    "verification_status": "Pending Verification"
                })

                # Avoid duplicates within the current run.
                seen_urls.add(url)

        except Exception as error:

            print(f"Search failed for {company}: {error}")

    return discovered


# ==================================================
# MAIN DISCOVERY PIPELINE
# ==================================================

def run_company_portal_discovery(selected_companies=None):

    existing_jobs = load_existing_jobs()
    seen_urls = load_seen_urls()

    # Also recover URLs from the existing job file.
    for job in existing_jobs:

        url = normalize_url(job.get("job_url", ""))

        if url:
            seen_urls.add(url)

    companies = COMPANIES

    if selected_companies:

        companies = {
            name: domains
            for name, domains in COMPANIES.items()
            if name.lower() in {
                item.lower() for item in selected_companies
            }
        }

    if not companies:
        print("No matching companies found.")
        return

    print("\n========== COMPANY PORTAL DISCOVERY ==========")
    print("Companies to search:", len(companies))
    print("Previously stored jobs:", len(existing_jobs))
    print("Previously seen URLs:", len(seen_urls))

    all_new_jobs = []

    for company, domains in companies.items():

        print(f"\n========== {company.upper()} ==========")

        new_jobs = discover_company_jobs(
            company,
            domains,
            seen_urls
        )

        print("New potential job leads:", len(new_jobs))

        all_new_jobs.extend(new_jobs)

        # Save progress after every company.
        if new_jobs:

            inserted, total = save_new_jobs(
                new_jobs,
                seen_urls
            )

            print("New records stored:", inserted)
            print("Total stored records:", total)

        else:
            # Persist previously seen URLs even if no new jobs.
            save_json(
                SEEN_URLS_FILE,
                sorted(seen_urls)
            )

    print("\n========== FINAL SUMMARY ==========")
    print("Companies searched:", len(companies))
    print("New potential leads found:", len(all_new_jobs))
    print("Total stored jobs:", len(load_existing_jobs()))
    print("Storage file:", JOBS_FILE)


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Discover jobs from reputed company career portals."
    )

    parser.add_argument(
        "--companies",
        nargs="*",
        help="Optionally search selected companies only."
    )

    args = parser.parse_args()

    run_company_portal_discovery(args.companies)
