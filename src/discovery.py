
import os
import json
import requests

from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

OUTPUT_FILE = Path("data/job_boards.json")
OLD_GREENHOUSE_FILE = Path("data/greenhouse_boards.json")

# Search only public ATS job-board domains.

# Search public ATS platforms for companies hiring
# graduates, freshers and interns in India.

SEARCH_CONFIG = {
    "greenhouse": {
        "domains": [
            "boards.greenhouse.io",
            "job-boards.greenhouse.io"
        ],
        "queries": [
            'India "new grad" software engineer Greenhouse',
            'India "graduate trainee" jobs Greenhouse',
            'India "entry level" software engineer Greenhouse',
            'India software engineering internship Greenhouse',
            'India fresher hiring technology companies Greenhouse'
        ]
    },
    "lever": {
        "domains": ["jobs.lever.co"],
        "queries": [
            'India "new grad" software engineer Lever',
            'India "graduate trainee" jobs Lever',
            'India "entry level" developer Lever',
            'India software engineering internship Lever',
            'India fresher hiring technology companies Lever'
        ]
    },
    "ashby": {
        "domains": ["jobs.ashbyhq.com"],
        "queries": [
            'India "new grad" software engineer Ashby',
            'India "graduate trainee" jobs Ashby',
            'India "entry level" developer Ashby',
            'India software engineering internship Ashby',
            'India fresher hiring technology companies Ashby'
        ]
    }
}



def extract_board_id(url, platform):
    """Extract the company board identifier from an ATS URL."""

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    parts = [part for part in parsed.path.split("/") if part]

    if not parts:
        return None

    if platform == "greenhouse":
        allowed_hosts = {
            "boards.greenhouse.io",
            "job-boards.greenhouse.io"
        }
    elif platform == "lever":
        allowed_hosts = {"jobs.lever.co"}
    elif platform == "ashby":
        allowed_hosts = {"jobs.ashbyhq.com"}
    else:
        return None

    if host not in allowed_hosts:
        return None

    # First path segment is the company board identifier.
    return parts[0]


def validate_board(platform, board_id):
    """Check whether a public ATS board API is accessible."""

    try:
        if platform == "greenhouse":
            url = (
                f"https://boards-api.greenhouse.io/v1/boards/"
                f"{board_id}/jobs"
            )
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            return isinstance(data.get("jobs"), list)

        elif platform == "lever":
            url = (
                f"https://api.lever.co/v0/postings/"
                f"{board_id}?mode=json"
            )
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            return isinstance(data, list)

        elif platform == "ashby":
            url = (
                f"https://api.ashbyhq.com/posting-api/job-board/"
                f"{board_id}"
            )
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
            return isinstance(data.get("jobs"), list)

    except (requests.RequestException, ValueError) as error:
        print(f"Validation failed for {platform}/{board_id}: {error}")

    return False


def discover_boards():
    """Discover company boards using Tavily."""

    discovered = {}

    for platform, config in SEARCH_CONFIG.items():

        print(f"\n========== {platform.upper()} DISCOVERY ==========")

        for query in config["queries"]:

            print("\nSearching:", query)

            try:
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=10,
                    include_domains=config["domains"]
                )

                results = response.get("results", [])

                print("Results found:", len(results))

                for result in results:

                    url = result.get("url", "")
                    if not url:
                        continue

                    board_id = extract_board_id(url, platform)

                    if not board_id:
                        continue

                    key = f"{platform}:{board_id}"

                    if key in discovered:
                        continue

                    print(f"Checking board: {platform}/{board_id}")

                    if validate_board(platform, board_id):
                        base_urls = {
                        "greenhouse": "https://boards.greenhouse.io",
                        "lever": "https://jobs.lever.co",
                        "ashby": "https://jobs.ashbyhq.com"
                        }

                        discovered[key] = {
                            "company": board_id,
                            "platform": platform,
                            "board_id": board_id,
                            "board_url": f"{base_urls[platform]}/{board_id}"
                        }

                        print("Valid board:", board_id)

            except Exception as error:
                print("Search failed:", error)

    return list(discovered.values())


def load_existing_greenhouse_boards():
    """Preserve previously discovered Greenhouse boards."""

    if not OLD_GREENHOUSE_FILE.exists():
        return []

    try:
        with open(OLD_GREENHOUSE_FILE, "r") as file:
            data = json.load(file)

        boards = []

        for board in data.get("greenhouse_boards", []):

            board_id = board.get("board_token")

            if not board_id:
                continue

            boards.append({
                "company": board.get("company", board_id),
                "platform": "greenhouse",
                "board_id": board_id,
                "board_url": (
                    f"https://boards.greenhouse.io/{board_id}"
                )
            })

        return boards

    except (OSError, json.JSONDecodeError) as error:
        print("Could not load old boards:", error)
        return []


def save_boards(boards):
    """Save unique validated boards."""

    unique_boards = {}

    for board in boards:
        key = f"{board['platform']}:{board['board_id']}"
        unique_boards[key] = board

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w") as file:
        json.dump(
            list(unique_boards.values()),
            file,
            indent=4
        )

    print("\n========== FINAL SUMMARY ==========")
    print("Total validated boards:", len(unique_boards))

    for platform in SEARCH_CONFIG:
        count = sum(
            1 for board in unique_boards.values()
            if board["platform"] == platform
        )
        print(f"{platform}: {count}")

    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":

    existing_boards = load_existing_greenhouse_boards()
    print("Existing Greenhouse boards:", len(existing_boards))

    new_boards = discover_boards()
    print("New boards discovered:", len(new_boards))

    all_boards = existing_boards + new_boards

    # Revalidate old boards before keeping them.
    validated_boards = [
        board for board in all_boards
        if validate_board(board["platform"], board["board_id"])
    ]

    save_boards(validated_boards)
