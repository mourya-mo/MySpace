
import os
import re
import requests
from dotenv import load_dotenv
from tavily import TavilyClient
import json
from pathlib import Path

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

query = 'site:job-boards.greenhouse.io India fresher jobs internships'

response = client.search(
    query=query,
    search_depth="basic",
    max_results=10
)

valid_boards = set()

for result in response.get("results", []):
    url = result.get("url", "")

    match = re.search(
        r"job-boards\.greenhouse\.io/([^/?#]+)",
        url
    )

    if match:
        board_token = match.group(1)

        api_url = (
            f"https://boards-api.greenhouse.io/v1/boards/"
            f"{board_token}/jobs"
        )

        try:
            check = requests.get(api_url, timeout=15)

            if check.status_code == 200:
                valid_boards.add(board_token)
                print("Valid board:", board_token)

        except requests.RequestException as error:
            print("Request failed:", board_token, error)

# Save discovered boards
data = {
    "greenhouse_boards": [
        {
            "board_token": token,
            "company": token.replace("-", " ").title(),
            "source": "Greenhouse"
        }
        for token in sorted(valid_boards)
    ]
}

file_path = Path("data/greenhouse_boards.json")
file_path.parent.mkdir(parents=True, exist_ok=True)

with open(file_path, "w") as file:
    json.dump(data, file, indent=4)

print("\nTotal valid boards:", len(valid_boards))
print("Boards saved to:", file_path)