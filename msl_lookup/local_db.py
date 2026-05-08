"""Local SQLite database for caching MSL lookups."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "msl_cache.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS msl_cache (
                mpn TEXT PRIMARY KEY,
                msl TEXT,
                package TEXT,
                manufacturer TEXT,
                description TEXT,
                looked_up_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lookup_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mpn TEXT,
                status TEXT,
                timestamp TEXT,
                error TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lookup_log_mpn ON lookup_log(mpn)")


def cache_msl(mpn: str, msl: str, package: str = None, manufacturer: str = None, description: str = None):
    from datetime import datetime

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO msl_cache (mpn, msl, package, manufacturer, description, looked_up_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (mpn, msl, package, manufacturer, description, datetime.now().isoformat()),
        )


def get_cached_msl(mpn: str):
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT msl, package, manufacturer, description FROM msl_cache WHERE mpn = ?",
            (mpn,),
        )
        return cur.fetchone()


def log_lookup(mpn: str, status: str, error: str = None):
    from datetime import datetime

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO lookup_log (mpn, status, timestamp, error) VALUES (?, ?, ?, ?)",
            (mpn, status, datetime.now().isoformat(), error),
        )


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
