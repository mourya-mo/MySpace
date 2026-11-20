
from datetime import datetime

from src.discovery import (
    load_existing_boards,
    discover_boards,
    save_boards
)

from src.collect_jobs import (
    collect_all_jobs,
    filter_fresher_jobs
)

from src.fresher_database import (
    create_fresher_tables,
    save_fresher_jobs
)

from src.classify_fresher_jobs import classify_pending_jobs


def run_daily_pipeline():

    start_time = datetime.now()

    print("\n======================================")
    print("       MYSPACE DAILY JOB PIPELINE")
    print("======================================")

    # 1. Ensure database tables exist.
    create_fresher_tables()

    # 2. Load previously discovered company boards.
    existing_boards = load_existing_boards()

    print("\nExisting company boards:", len(existing_boards))

    # 3. Discover additional company boards.
    new_boards = discover_boards()

    print("New boards discovered:", len(new_boards))

    # 4. Merge and preserve all company boards.
    save_boards(existing_boards + new_boards)

    # 5. Collect jobs from all known boards.
    all_jobs = collect_all_jobs()

    print("\nTotal jobs collected:", len(all_jobs))

    # 6. Apply India and fresher eligibility filters.
    fresher_jobs = filter_fresher_jobs(all_jobs)

    print("Jobs passed to database:", len(fresher_jobs))

    # 7. Insert new jobs and update existing postings.
    saved = save_fresher_jobs(fresher_jobs)

    print("New or updated records:", saved)

    # 8. Validate pending jobs using Groq.
    print("\nStarting Groq classification...")

    classify_pending_jobs()

    end_time = datetime.now()
    duration = end_time - start_time

    print("\n======================================")
    print("       PIPELINE COMPLETED")
    print("======================================")
    print("Started:", start_time)
    print("Completed:", end_time)
    print("Duration:", duration)
    print("======================================")


if __name__ == "__main__":
    run_daily_pipeline()
