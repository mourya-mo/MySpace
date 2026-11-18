import sqlite3
from pathlib import Path
DATABASE_NAME=Path("data/jobs.db")
DATABASE_NAME.parent.mkdir(parents=True,exist_ok=True)

def get_connection():
    """ create a connection to sqlite database"""
    connection=sqlite3.connect(DATABASE_NAME)
    connection.row_factory=sqlite3.Row
    return connection
def add_missing_columns():
    create_tables()
    connection = get_connection()

    existing_columns = [
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(jobs)"
        ).fetchall()
    ]

    if "experience_level" not in existing_columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN experience_level TEXT"
        )

    if "fresher_eligible" not in existing_columns:
        connection.execute(
            "ALTER TABLE jobs ADD COLUMN fresher_eligible INTEGER"
        )

    connection.commit()
    connection.close()
def create_tables():
    """create the job table if it doesnot exist"""
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            job_description TEXT,
            job_url TEXT UNIQUE,
            source TEXT,
            role_category TEXT,
            job_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_jobs(jobs):
    """Save collected jobs into the SQLite database."""

    connection = get_connection()

    query = """
        INSERT OR IGNORE INTO jobs (
            job_title,
            company,
            location,
            job_description,
            job_url,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """

    job_data = []

    for job in jobs:
        row = (
            job.get("job_title"),
            job.get("company"),
            job.get("location"),
            job.get("job_description"),
            job.get("job_url"),
            job.get("source")
        )

        job_data.append(row)  # Must be INSIDE the loop

    connection.executemany(query, job_data)
    connection.commit()

    saved_count = connection.total_changes

    connection.close()

    return saved_count



if __name__ == "__main__":
    create_tables()
    add_missing_columns()
    print("Database and jobs table created successfully!")