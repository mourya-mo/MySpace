
import os
import re
import sqlite3
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_PATH = ROOT / "data" / "fresher_jobs.db"

MODEL_NAME = "openai/gpt-oss-120b"


# ---------------- FIND JOBS ----------------

def find_relevant_jobs(query, limit=5):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Extract useful search terms
    words = re.findall(r"[a-zA-Z0-9+#.]+", query.lower())

    stop_words = {
        "find", "show", "give", "me", "jobs", "job",
        "internships", "internship", "looking", "for",
        "the", "in", "with", "and", "any", "are",
        "available", "opportunities"
    }

    keywords = [
        word for word in words
        if word not in stop_words and len(word) > 1
    ]

    if not keywords:
        keywords = ["python", "developer"]

    conditions = []
    params = []

    for word in keywords:
        conditions.append("""
            (
                job_title LIKE ?
                OR company LIKE ?
                OR location LIKE ?
                OR job_description LIKE ?
            )
        """)

        pattern = f"%{word}%"
        params.extend([pattern] * 4)

    sql = f"""
        SELECT
            id,
            job_title,
            company,
            location,
            job_description,
            job_url,
            experience_level
        FROM fresher_jobs
        WHERE lower(COALESCE(experience_level, '')) != 'unclear'
        AND (
            {" OR ".join(conditions)}
        )
        ORDER BY id DESC
        LIMIT ?
    """

    params.append(limit)

    jobs = conn.execute(sql, params).fetchall()
    conn.close()

    return [dict(job) for job in jobs]


# ---------------- GROQ RESPONSE ----------------

def get_ai_response(message, conversation_history=None):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "Groq API key was not found. Please check your .env file."

    try:
        client = Groq(api_key=api_key)

        # Retrieve actual jobs from MySpace
        jobs = find_relevant_jobs(message)

        if jobs:
            job_context = ""

            for job in jobs:
                job_context += f"""
Job ID: {job['id']}
Title: {job['job_title']}
Company: {job['company']}
Location: {job['location']}
Opportunity Type: {job['experience_level']}
Description: {str(job['job_description'] or '')[:1200]}
Application Link: {job['job_url']}

--------------------
"""
        else:
            job_context = "No matching jobs were found in the database."

        system_prompt = f"""
You are MySpace AI, the career assistant of the MySpace job portal.

YOUR PURPOSE:
Help users discover fresher jobs and internships in India and guide
them with job-related career questions.

SCOPE:
You can help with:
1. Finding jobs and internships from the MySpace database.
2. Explaining job descriptions and eligibility.
3. Understanding required skills and technologies.
4. Resume improvement and job preparation.
5. Interview preparation.
6. Career guidance for freshers.
7. Understanding job roles and responsibilities.

STRICT RULES:
- You are NOT a general-purpose chatbot.
- Only answer questions related to jobs, internships, careers,
  skills, resumes and interview preparation.
- If a question is unrelated, politely say:
  "I'm MySpace AI, here to help with jobs, internships and career
  guidance. Let's focus on your career goals!"
- Never invent job listings, companies, salaries or application links.
- Recommend only jobs provided in the MySpace database context.
- If no matching jobs are found, clearly say that no matching
  opportunities were found in our current listings.
- Do not claim that a job is available if the database does not
  confirm it.
- For general career questions, provide helpful advice without
  pretending it came from the database.

CONVERSATION STYLE:
- Keep answers simple, clear and conversational.
- Sound like a helpful career advisor, not a formal AI robot.
- Prefer short paragraphs and bullet points.
- Avoid unnecessary technical explanations.
- Do not repeat the user's question.
- Ask only one follow-up question when more information is needed.
- Give practical answers instead of lengthy generic advice.

Always stay within the MySpace career-assistance purpose.

MYSPACE JOB DATABASE:
{job_context}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # Include recent conversation context
        if conversation_history:
            messages.extend(conversation_history[-6:])

        messages.append({
            "role": "user",
            "content": message
        })

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.4,
            max_tokens=1000
        )

        return response.choices[0].message.content

    except Exception as error:
        return f"Unable to get an AI response. Please check the Groq configuration. Details: {error}"

