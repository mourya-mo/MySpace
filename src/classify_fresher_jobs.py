
import os
import json
import time

from dotenv import load_dotenv
from groq import Groq

from src.fresher_database import get_fresher_connection


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(
    api_key=api_key,
    max_retries=0
)

MODEL = "openai/gpt-oss-120b"

BATCH_SIZE = 5
MAX_RETRIES = 3


# --------------------------------------------------
# 1. CLASSIFY JOBS USING GROQ
# --------------------------------------------------

def classify_batch_with_groq(jobs):

    job_details = []

    for job in jobs:

        job_details.append({
            "id": job["id"],
            "title": job["job_title"],
            "company": job["company"],
            "location": job["location"],
            "description": (job["job_description"] or "")[:2500]
        })

    prompt = f"""
You are an expert recruitment and job eligibility classifier.

Your task is to determine whether each job is genuinely suitable
for candidates with 0 to 2 years of professional experience,
including fresh graduates.

JOBS:
{json.dumps(job_details, ensure_ascii=False)}

Return ONLY valid JSON in this exact structure:

{{
    "classifications": [
        {{
            "id": 123,
            "decision": "Eligible",
            "experience_level": "Fresher",
            "min_experience": 0,
            "max_experience": 2,
            "reason": "The posting explicitly accepts candidates with 0-2 years."
        }}
    ]
}}

DECISION RULES:

1. Return exactly one classification for every input job.
2. Preserve the exact job ID.
3. Only approve jobs genuinely suitable for candidates with
   0 to 2 years of experience.

4. Experience eligibility:
   - 0 years: Eligible.
   - 0-1 years: Eligible.
   - 1-2 years: Eligible.
   - Exactly 2 years: Eligible.
   - 2-3 years: Not eligible.
   - 2-5 years: Not eligible.
   - 3+ years: Not eligible.
   - 2+ years: Not eligible because the upper limit is not restricted to 2.
   - 0-3 years: Not eligible.

5. Internship positions can be Eligible when they are genuinely
   internship opportunities and do not require experience beyond
   the 0-2 year limit.

6. Do not assume Associate, Junior, Engineer, Analyst or Trainee
   automatically means fresher-friendly.

7. Exclude positions clearly intended for senior or experienced
   professionals, including Senior, Staff, Principal, Lead,
   Manager, Director and Architect positions.

8. Do not confuse years of experience required with years of
   company experience, company history, product history or
   unrelated numbers.

9. If experience is not mentioned:
   - Approve only when the description clearly indicates that
     fresh graduates or candidates with no experience can apply.
   - An explicit internship opportunity can qualify.
   - Otherwise return Unclear.

10. Do not invent experience requirements.

11. Use these exact decision values:
    Eligible, Not eligible, Unclear.

12. experience_level must be:
    Fresher, Internship, Experienced or Unclear.

13. min_experience and max_experience must be numeric or null.
    Use null when the requirement cannot be determined.

14. Give a short reason based on the job description.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify job eligibility carefully. "
                    "Never assume missing information. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(
        response.choices[0].message.content
    )

    return result["classifications"], response.usage


# --------------------------------------------------
# 2. VALIDATE GROQ RESPONSE
# --------------------------------------------------

def validate_results(jobs, results):

    expected_ids = {
        job["id"] for job in jobs
    }

    received_ids = [
        item.get("id") for item in results
    ]

    if len(results) != len(jobs):
        raise ValueError(
            "Incorrect number of classifications"
        )

    if len(set(received_ids)) != len(received_ids):
        raise ValueError("Duplicate job IDs in response")

    if set(received_ids) != expected_ids:
        raise ValueError(
            "Missing or incorrect job IDs"
        )

    valid_decisions = {
        "Eligible",
        "Not eligible",
        "Unclear"
    }

    valid_levels = {
        "Fresher",
        "Internship",
        "Experienced",
        "Unclear"
    }

    for item in results:

        if item.get("decision") not in valid_decisions:
            raise ValueError("Invalid eligibility decision")

        if item.get("experience_level") not in valid_levels:
            raise ValueError("Invalid experience level")

        for field in ["min_experience", "max_experience"]:

            value = item.get(field)

            if value is not None:
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or value < 0
                ):
                    raise ValueError(
                        f"Invalid {field} for job {item['id']}"
                    )


# --------------------------------------------------
# 3. SAVE GROQ CLASSIFICATIONS
# --------------------------------------------------

def save_classifications(connection, results):

    eligible = 0
    excluded = 0
    unclear = 0

    for item in results:

        job_id = item["id"]
        decision = item["decision"]

        if decision == "Eligible":

            # Extra safeguard against ranges exceeding 2 years.
            minimum = item.get("min_experience")
            maximum = item.get("max_experience")

            if minimum is not None and minimum > 2:
                decision = "Not eligible"

            elif maximum is not None and maximum > 2:
                decision = "Not eligible"

            elif minimum is not None and maximum is None:
                decision = "Unclear"

        if decision == "Eligible":

            level = item["experience_level"]

            if level not in {"Fresher", "Internship"}:
                level = "Fresher"

            connection.execute("""
                UPDATE fresher_jobs
                SET experience_level = ?,
                    min_experience = ?,
                    max_experience = ?,
                    classification_source = 'Groq'
                WHERE id = ?
            """, (
                level,
                item.get("min_experience"),
                item.get("max_experience"),
                job_id
            ))

            eligible += 1

            print(
                "ELIGIBLE:",
                job_id,
                "|",
                item.get("reason", "")
            )

        elif decision == "Not eligible":

            connection.execute("""
                DELETE FROM fresher_jobs
                WHERE id = ?
            """, (job_id,))

            excluded += 1

            print(
                "EXCLUDED:",
                job_id,
                "|",
                item.get("reason", "")
            )

        else:

            connection.execute("""
                UPDATE fresher_jobs
                SET experience_level = 'Unclear',
                    classification_source = 'Pending Manual Review'
                WHERE id = ?
            """, (job_id,))

            unclear += 1

            print(
                "UNCLEAR:",
                job_id,
                "|",
                item.get("reason", "")
            )

    connection.commit()

    return eligible, excluded, unclear


# --------------------------------------------------
# 4. CLASSIFY ONLY PENDING JOBS
# --------------------------------------------------

def classify_pending_jobs():

    connection = get_fresher_connection()

    total_eligible = 0
    total_excluded = 0
    total_unclear = 0
    failed = 0

    total_input_tokens = 0
    total_output_tokens = 0

    try:

        jobs = connection.execute("""
            SELECT *
            FROM fresher_jobs
            WHERE classification_source = 'Pending Groq'
               OR experience_level = 'Unclear'
            ORDER BY id
        """).fetchall()

        total_jobs = len(jobs)

        print("\n========== GROQ FRESHER VALIDATION ==========")
        print("Pending jobs:", total_jobs)
        print("Batch size:", BATCH_SIZE)

        if total_jobs == 0:
            print("No pending jobs to validate.")
            return

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

                    results, usage = classify_batch_with_groq(
                        batch
                    )

                    validate_results(batch, results)

                    eligible, excluded, unclear = (
                        save_classifications(
                            connection,
                            results
                        )
                    )

                    total_eligible += eligible
                    total_excluded += excluded
                    total_unclear += unclear

                    total_input_tokens += usage.prompt_tokens
                    total_output_tokens += usage.completion_tokens

                    print("Batch completed successfully.")
                    print("Eligible:", eligible)
                    print("Excluded:", excluded)
                    print("Unclear:", unclear)

                    batch_success = True

                    # Short pause between successful batches.
                    if start + BATCH_SIZE < total_jobs:
                        time.sleep(5)

                    break

                except Exception as error:

                    status_code = getattr(
                        error,
                        "status_code",
                        None
                    )

                    wait_time = min(20 * attempt, 60)

                    print(
                        f"Attempt {attempt}/{MAX_RETRIES} failed: "
                        f"{error}"
                    )

                    if attempt < MAX_RETRIES:
                        if status_code == 429:
                            print(
                                f"Rate limit reached. "
                                f"Waiting {wait_time} seconds..."
                            )
                        else:
                            print(
                                f"Retrying in {wait_time} seconds..."
                            )

                        time.sleep(wait_time)

            if not batch_success:

                failed += len(batch)

                print(
                    "Batch failed. Its records remain in the database."
                )

        remaining = connection.execute("""
            SELECT COUNT(*)
            FROM fresher_jobs
        """).fetchone()[0]

        print("\n========== FINAL GROQ SUMMARY ==========")
        print("Jobs processed:", total_jobs)
        print("Groq eligible:", total_eligible)
        print("Excluded:", total_excluded)
        print("Pending manual review:", total_unclear)
        print("Failed jobs:", failed)
        print("Input tokens:", total_input_tokens)
        print("Output tokens:", total_output_tokens)
        print("Remaining database jobs:", remaining)

    finally:
        connection.close()


# --------------------------------------------------
# 5. EXECUTION
# --------------------------------------------------

if __name__ == "__main__":
    classify_pending_jobs()

