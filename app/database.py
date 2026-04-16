import sqlite3
import os
import logging
from contextlib import contextmanager
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bot_history.db")

@contextmanager
def get_db_conn():
    """Context manager for sqlite3 connections."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    try:
        yield conn
    finally:
        conn.close()

def db_init():
    """Initialize the database and create tables if they don't exist."""
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            # source_id: Unique identifier from source (URL or news ID)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT UNIQUE,
                    content TEXT,
                    platform_url TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Database init error: {e}")

def is_already_posted(source_id: str) -> bool:
    """Check if a source_id has already been posted."""
    if not source_id:
        return False
    
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM posts_history WHERE source_id = ?", (source_id,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return False

def log_post(source_id: str, content: str, platform_url: str = ""):
    """Log a successful post to history."""
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO posts_history (source_id, content, platform_url) VALUES (?, ?, ?)",
                (source_id, content, platform_url)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Database log error: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_init()
