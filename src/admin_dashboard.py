
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

JOBS_DB = ROOT / "data" / "fresher_jobs.db"
AUTH_DB = ROOT / "data" / "myspace.db"


def get_dashboard_stats():

    jobs_conn = sqlite3.connect(JOBS_DB)
    users_conn = sqlite3.connect(AUTH_DB)

    jobs_cursor = jobs_conn.cursor()
    users_cursor = users_conn.cursor()

    # Total jobs
    jobs_cursor.execute("SELECT COUNT(*) FROM fresher_jobs")
    total_jobs = jobs_cursor.fetchone()[0]

    # Jobs added today (India time)
    jobs_cursor.execute("""
        SELECT COUNT(*)
        FROM fresher_jobs
        WHERE date(created_at, '+5 hours', '+30 minutes')
              = date('now', '+5 hours', '+30 minutes')
    """)
    jobs_today = jobs_cursor.fetchone()[0]

    # Total registered users
    users_cursor.execute("SELECT COUNT(*) FROM users")
    total_users = users_cursor.fetchone()[0]

    # Active users in the last 30 days
    users_cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE is_active = 1
        AND last_login >= datetime('now', '-30 days')
    """)
    active_users = users_cursor.fetchone()[0]

    jobs_conn.close()
    users_conn.close()

    return {
        "total_jobs": total_jobs,
        "jobs_today": jobs_today,
        "total_users": total_users,
        "active_users": active_users
    }


def get_daily_job_counts():

    conn = sqlite3.connect(JOBS_DB)

    query = """
        SELECT
            date(created_at, '+5 hours', '+30 minutes') AS job_date,
            COUNT(*) AS jobs_added
        FROM fresher_jobs
        WHERE created_at IS NOT NULL
        GROUP BY job_date
        ORDER BY job_date DESC
        LIMIT 14
    """

    import pandas as pd
    df = pd.read_sql_query(query, conn)

    conn.close()

    return df.sort_values("job_date")


def get_all_users():

    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row

    users = conn.execute("""
        SELECT id, full_name, email, role,
               created_at, last_login, is_active
        FROM users
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return [dict(user) for user in users]


def update_user_status(user_id, is_active):

    conn = sqlite3.connect(AUTH_DB)

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET is_active = ?
        WHERE id = ?
        AND role != 'admin'
    """, (int(is_active), user_id))

    conn.commit()
    changed = cursor.rowcount
    conn.close()

    return changed > 0
