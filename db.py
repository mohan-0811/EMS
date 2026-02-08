import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ems.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
SEED_PATH = Path(__file__).resolve().parent / "seed.sql"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with conn:
        conn.executescript(SCHEMA_PATH.read_text())
        existing = conn.execute("SELECT COUNT(*) AS count FROM resources").fetchone()["count"]
        if existing == 0:
            conn.executescript(SEED_PATH.read_text())
    conn.close()
