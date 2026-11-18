
from src.fresher_classifier import (
    clean_description,
    extract_experience,
    classify_experience
)

from src.fresher_database import get_fresher_connection


def audit_fresher_jobs():

    connection = get_fresher_connection()

    counts = {
        "Eligible": 0,
        "Not eligible": 0,
        "Unclear": 0
    }

    try:
        jobs = connection.execute("""
            SELECT
                id,
                job_title,
                company,
                job_description,
                job_url
            FROM fresher_jobs
        """).fetchall()

        print("Total jobs to audit:", len(jobs))

        for job in jobs:

            description = clean_description(
                job["job_description"]
            )

            result = classify_experience(
                job["job_title"],
                description
            )

            experience = extract_experience(description)

            counts[result] += 1

            if result == "Not eligible":

                # Remove clearly ineligible jobs.
                connection.execute("""
                    DELETE FROM fresher_jobs
                    WHERE id = ?
                """, (job["id"],))

                print(
                    "EXCLUDED:",
                    job["job_title"],
                    "|",
                    job["company"]
                )

            elif result == "Unclear":

                # Keep the record for Groq validation.
                connection.execute("""
                    UPDATE fresher_jobs
                    SET experience_level = 'Unclear',
                        classification_source = 'Pending Groq'
                    WHERE id = ?
                """, (job["id"],))

            else:

                # Retain confirmed first-pass eligible jobs.
                level = (
                    "Internship"
                    if "intern" in job["job_title"].lower()
                    else "Fresher"
                )

                connection.execute("""
                    UPDATE fresher_jobs
                    SET experience_level = ?,
                        min_experience = ?,
                        max_experience = ?,
                        classification_source = 'Python'
                    WHERE id = ?
                """, (
                    level,
                    experience["min_years"],
                    experience["max_years"],
                    job["id"]
                ))

        connection.commit()

        print("\n========== AUDIT SUMMARY ==========")
        print("Originally audited:", len(jobs))
        print("Eligible:", counts["Eligible"])
        print("Clearly ineligible:", counts["Not eligible"])
        print("Pending Groq validation:", counts["Unclear"])

        remaining = connection.execute("""
            SELECT COUNT(*) FROM fresher_jobs
        """).fetchone()[0]

        print("Remaining in fresher database:", remaining)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    audit_fresher_jobs()
