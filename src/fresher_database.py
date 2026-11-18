
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

        connection.commit()
        print("Fresher database table created successfully.")

    finally:
        connection.close()


def save_fresher_jobs(jobs):
    connection = get_fresher_connection()
    saved = 0

    try:
        for job in jobs:
            cursor = connection.execute("""
                INSERT OR IGNORE INTO fresher_jobs (
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

            saved += cursor.rowcount

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return saved
