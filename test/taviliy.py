
import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Load API key from .env
load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError("TAVILY_API_KEY not found in .env")

# Initialize Tavily
client = TavilyClient(api_key=api_key)

# Search for Greenhouse job boards in India
query = 'site:job-boards.greenhouse.io India fresher jobs internships'

response = client.search(
    query=query,
    search_depth="basic",
    max_results=10
)

# Display search results
results = response.get("results", [])

print("Total results:", len(results))

for result in results:
    print("\nTitle:", result.get("title"))
    print("URL:", result.get("url"))
    print("Score:", result.get("score"))
