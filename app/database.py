import sqlite3
import os
from datetime import datetime

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bot_history.db")

def db_init():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # post_id: Unique identifier from source (URL or news ID)
    # content_hash: To detect if same news was re-written
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
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def is_already_posted(source_id: str) -> bool:
    """Check if a source_id has already been posted."""
    if not source_id:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM posts_history WHERE source_id = ?", (source_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def log_post(source_id: str, content: str, platform_url: str = ""):
    """Log a successful post to history."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO posts_history (source_id, content, platform_url) VALUES (?, ?, ?)",
            (source_id, content, platform_url)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database log error: {e}")

if __name__ == "__main__":
    db_init()
