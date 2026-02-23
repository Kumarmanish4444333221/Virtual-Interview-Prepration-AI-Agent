"""
Interview History Module
Stores and retrieves past interview sessions per user using SQLite.
"""
import os
import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path (shared directory with auth)
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "interviews.db")


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection, creating the database if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the interviews database table."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                experience_level TEXT NOT NULL,
                fit_score INTEGER NOT NULL,
                num_questions INTEGER NOT NULL,
                summary TEXT,
                transcript TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_interview(
    username: str,
    company: str,
    role: str,
    experience_level: str,
    fit_score: int,
    num_questions: int,
    summary: str,
    transcript: Optional[List] = None,
) -> int:
    """
    Save a completed interview session.

    Args:
        username: The authenticated user's identifier
        company: Target company
        role: Target role
        experience_level: Experience level
        fit_score: Resume fit score (0-100)
        num_questions: Number of questions asked
        summary: AI-generated interview summary
        transcript: List of (speaker, message) tuples

    Returns:
        The ID of the saved interview record
    """
    conn = _get_connection()
    try:
        transcript_json = json.dumps(transcript or [])
        cursor = conn.execute(
            """INSERT INTO interviews
               (username, company, role, experience_level, fit_score, num_questions, summary, transcript, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                username,
                company,
                role,
                experience_level,
                fit_score,
                num_questions,
                summary,
                transcript_json,
                datetime.now(tz=timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        logger.info("Saved interview %d for user %s", cursor.lastrowid, username)
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_interviews(username: str, limit: int = 20) -> List[Dict]:
    """
    Retrieve a user's past interviews, most recent first.

    Args:
        username: User identifier
        limit: Maximum number of records to return

    Returns:
        List of interview dicts
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT id, company, role, experience_level, fit_score, num_questions, summary, created_at
               FROM interviews WHERE username = ? ORDER BY created_at DESC LIMIT ?""",
            (username, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_interview_detail(interview_id: int, username: str) -> Optional[Dict]:
    """
    Retrieve full details of a single interview (including transcript).

    Args:
        interview_id: Interview record ID
        username: User identifier (for ownership check)

    Returns:
        Interview dict or None
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM interviews WHERE id = ? AND username = ?",
            (interview_id, username),
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["transcript"] = json.loads(result.get("transcript") or "[]")
        return result
    finally:
        conn.close()


def get_user_stats(username: str) -> Dict:
    """
    Compute aggregate statistics for a user.

    Returns:
        Dict with total_interviews, avg_score, companies_practiced, best_score
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            """SELECT COUNT(*) as total,
                      COALESCE(AVG(fit_score), 0) as avg_score,
                      COALESCE(MAX(fit_score), 0) as best_score,
                      COUNT(DISTINCT company) as companies
               FROM interviews WHERE username = ?""",
            (username,),
        ).fetchone()
        return {
            "total_interviews": row["total"],
            "avg_score": round(row["avg_score"], 1),
            "best_score": row["best_score"],
            "companies_practiced": row["companies"],
        }
    finally:
        conn.close()


# Ensure tables exist on module import
init_db()
