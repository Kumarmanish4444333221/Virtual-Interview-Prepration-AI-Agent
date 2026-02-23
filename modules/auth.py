"""
Authentication Module
Handles user registration and login with SQLite backend and bcrypt password hashing.
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "users.db")


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection, creating the database if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the users database table."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def register_user(username: str, password: str, display_name: Optional[str] = None) -> bool:
    """
    Register a new user.

    Args:
        username: Unique username
        password: Plain-text password (will be hashed)
        display_name: Optional display name

    Returns:
        True if registration succeeded, False if username already exists
    """
    conn = _get_connection()
    try:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn.execute(
            "INSERT INTO users (username, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, display_name or username, datetime.now(tz=timezone.utc).isoformat()),
        )
        conn.commit()
        logger.info("Registered new user: %s", username)
        return True
    except sqlite3.IntegrityError:
        logger.warning("Registration failed – username already exists: %s", username)
        return False
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user by username and password.

    Args:
        username: Username
        password: Plain-text password

    Returns:
        User dict on success, None on failure
    """
    conn = _get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row is None:
            return None

        if bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            # Update last_login timestamp
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(tz=timezone.utc).isoformat(), row["id"]),
            )
            conn.commit()
            return {
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"],
                "created_at": row["created_at"],
            }
        return None
    finally:
        conn.close()


def user_exists(username: str) -> bool:
    """Check whether a username is already registered."""
    conn = _get_connection()
    try:
        row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        return row is not None
    finally:
        conn.close()


# Ensure tables exist on module import
init_db()
