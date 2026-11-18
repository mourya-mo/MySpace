
import os
import json
import time

from dotenv import load_dotenv
from groq import Groq
from src.database import get_connection

# Load environment variables
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    max_retries=0
)

MODEL = "openai/gpt-oss-120b"
BATCH_SIZE = 10
MAX_RETRIES = 3
TPM_LIMIT = 8000


def classify_batch_with_groq(jobs):

    job_details = []

    for job in jobs:
        job_details.append({
            "id": job["id"],
            "title": job["job_title"],
            "company": job["company"],
            "location": job["location"],
            "description": (job["job_description"] or "")[:1200]
        })

    prompt = f"""
    You are an expert job classification assistant.

    Classify each of the following job postings.

    JOBS:
    {json.dumps(job_details, ensure_ascii=False)}

    Return ONLY valid JSON in this exact structure:

    {{
        "classifications": [
            {{
                "id": 123,
                "role_category": "Software Engineering",
                "experience_level": "Fresher",
                "job_type": "Full-time",
                "fresher_eligible": true
            }}
        ]
    }}

    RULES:

    1. Preserve the exact ID of every job.
    2. Return exactly one classification per input job.
    3. Role categories must be one of:
       Software Engineering, Data Science, AI-ML, DevOps, Other.

    4. Experience levels must be one of:
       Fresher, Internship, Experienced, Unclear.

    5. Job types must be one of:
       Internship, Full-time, Contract, Other.

    6. Do not assume Associate means fresher-friendly.
    7. Internship positions must have job_type as Internship.
    8. Jobs requiring 2 or more years of experience should be
       classified as Experienced.
    9. If experience requirements are unclear, use Unclear.
    10. Set fresher_eligible to true only when the description
        supports applications from fresh graduates or candidates
        with no experience.
    11. Do not invent missing information.
    12. Return classifications for all input jobs.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Classify job postings accurately. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    return result["classifications"], response.usage


def validate_results(jobs, results):

    expected_ids = {job["id"] for job in jobs}
    received_ids = [item.get("id") for item in results]

    if len(results) != len(jobs):
        raise ValueError("Incorrect number of classifications")

    if set(received_ids) != expected_ids:
        raise ValueError("Missing or incorrect job IDs")

    valid_roles = {
        "Software Engineering",
        "Data Science",
        "AI-ML",
        "DevOps",
        "Other"
    }

    valid_experience = {
        "Fresher",
        "Internship",
        "Experienced",
        "Unclear"
    }

    valid_types = {
        "Internship",
        "Full-time",
        "Contract",
        "Other"
    }

    for item in results:

        if item.get("role_category") not in valid_roles:
            raise ValueError("Invalid role category")

        if item.get("experience_level") not in valid_experience:
            raise ValueError("Invalid experience level")

        if item.get("job_type") not in valid_types:
            raise ValueError("Invalid job type")

        if not isinstance(item.get("fresher_eligible"), bool):
            raise ValueError("Invalid fresher eligibility value")


def save_classifications(connection, results):

    query = """
        UPDATE jobs
        SET role_category = ?,
            job_type = ?,
            experience_level = ?,
            fresher_eligible = ?
        WHERE id = ?
    """

    for item in results:

        connection.execute(
            query,
            (
                item["role_category"],
                item["job_type"],
                item["experience_level"],
                int(item["fresher_eligible"]),
                item["id"]
            )
        )

    connection.commit()


def classify_all_india_jobs():

    connection = get_connection()

    try:

        jobs = connection.execute("""
            SELECT *
            FROM jobs
            WHERE LOWER(location) LIKE '%india%'
            AND experience_level IS NULL
            ORDER BY id
        """).fetchall()

        total_jobs = len(jobs)

        print("Unclassified India jobs:", total_jobs)
        print("Batch size:", BATCH_SIZE)

        successful = 0
        failed = 0

        total_input_tokens = 0
        total_output_tokens = 0

        for start in range(0, total_jobs, BATCH_SIZE):

            batch = jobs[start:start + BATCH_SIZE]
            batch_number = (start // BATCH_SIZE) + 1

            print(
                f"\nProcessing batch {batch_number} "
                f"({len(batch)} jobs)..."
            )

            batch_success = False

            for attempt in range(1, MAX_RETRIES + 1):

                try:

                    results, usage = classify_batch_with_groq(batch)

                    validate_results(batch, results)

                    save_classifications(connection, results)

                    successful += len(results)

                    total_input_tokens += usage.prompt_tokens
                    total_output_tokens += usage.completion_tokens

                    print("Batch completed successfully!")
                    print("Input tokens:", usage.prompt_tokens)
                    print("Output tokens:", usage.completion_tokens)

                    batch_success = True

                    # Wait based on estimated token consumption.
                    total_tokens = (
                        usage.prompt_tokens + usage.completion_tokens
                    )

                    wait_time = (total_tokens / TPM_LIMIT) * 60 + 5

                    print(
                        f"Waiting {wait_time:.0f} seconds "
                        "to respect the token limit..."
                    )

                    time.sleep(wait_time)

                    break

                except Exception as error:

                    status_code = getattr(error, "status_code", None)

                    if status_code == 429:

                        wait_time = min(65 * attempt, 180)

                        print("Groq rate limit reached.")
                        print(
                            f"Retry {attempt}/{MAX_RETRIES}. "
                            f"Waiting {wait_time} seconds..."
                        )

                        if attempt < MAX_RETRIES:
                            time.sleep(wait_time)

                    else:

                        print(f"Attempt {attempt} failed: {error}")

                        if attempt < MAX_RETRIES:
                            time.sleep(5)

            if not batch_success:

                failed += len(batch)

                print("Batch failed. Moving to next batch.")

        print("\n========== CLASSIFICATION SUMMARY ==========")
        print("Total jobs:", total_jobs)
        print("Successfully classified:", successful)
        print("Failed jobs:", failed)
        print("Input tokens:", total_input_tokens)
        print("Output tokens:", total_output_tokens)

    finally:
        connection.close()


if __name__ == "__main__":
    classify_all_india_jobs()
