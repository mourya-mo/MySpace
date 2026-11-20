
import sqlite3
from pathlib import Path

DB_PATH = Path("data/fresher_jobs.db")


def get_fresher_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def create_fresher_tables():
    connection = get_fresher_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS fresher_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                job_description TEXT,
                job_url TEXT UNIQUE,
                source TEXT,
                experience_level TEXT,
                min_experience REAL,
                max_experience REAL,
                classification_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS rejected_fresher_jobs (
                id INTEGER PRIMARY KEY,
                job_title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                job_description TEXT,
                job_url TEXT,
                source TEXT,
                experience_level TEXT,
                min_experience REAL,
                max_experience REAL,
                classification_source TEXT,
                created_at TIMESTAMP,
                rejection_reason TEXT,
                rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()
        print("Fresher database tables created successfully.")

    finally:
        connection.close()



def save_fresher_jobs(jobs):
    connection = get_fresher_connection()
    saved = 0
    updated = 0

    try:
        for job in jobs:

            # Check whether this job URL already exists.
            existing = connection.execute("""
                SELECT 1
                FROM fresher_jobs
                WHERE job_url = ?
            """, (job["job_url"],)).fetchone()

            cursor = connection.execute("""
                INSERT INTO fresher_jobs (
                    job_title,
                    company,
                    location,
                    job_description,
                    job_url,
                    source,
                    experience_level,
                    min_experience,
                    max_experience,
                    classification_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(job_url) DO UPDATE SET
                    job_title = excluded.job_title,
                    company = excluded.company,
                    location = excluded.location,
                    job_description = excluded.job_description,
                    source = excluded.source

                WHERE
                    fresher_jobs.job_title IS NOT excluded.job_title
                    OR fresher_jobs.company IS NOT excluded.company
                    OR fresher_jobs.location IS NOT excluded.location
                    OR fresher_jobs.job_description IS NOT excluded.job_description
                    OR fresher_jobs.source IS NOT excluded.source
            """, (
                job["job_title"],
                job["company"],
                job["location"],
                job["job_description"],
                job["job_url"],
                job["source"],
                job["experience_level"],
                job.get("min_experience"),
                job.get("max_experience"),
                job.get("classification_source")
            ))

            if cursor.rowcount == 1:
                if existing:
                    updated += 1
                else:
                    saved += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    print(f"New jobs inserted: {saved}")
    print(f"Existing jobs updated: {updated}")

    return saved + updated


