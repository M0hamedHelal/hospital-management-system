"""
Database layer for the Hospital Management System.

Uses SQLite (Python's built-in sqlite3 module) so the project needs
zero external database server. The file `hospital.db` is created
automatically, next to this file, the first time the app runs.

Tables:
    doctors           - one row per doctor
    patients          - one row per patient
    appointments      - one row per booking. UNIQUE(doctor_id, slot, date)
                        is what actually prevents double-booking a doctor
                        on the SAME date + time (this was the main bug in
                        the original in-memory version: slots were blocked
                        globally instead of per-date).
    medical_records   - prescriptions/notes written after a completed visit
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "hospital.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS doctors (
    id             TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    age            INTEGER NOT NULL,
    national_id    TEXT NOT NULL UNIQUE,
    phone          TEXT NOT NULL,
    specialization TEXT NOT NULL,
    start_time     TEXT NOT NULL,
    end_time       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patients (
    id             TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    age            INTEGER NOT NULL,
    national_id    TEXT NOT NULL UNIQUE,
    phone          TEXT NOT NULL,
    blood_type     TEXT NOT NULL,
    problem        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id   TEXT NOT NULL REFERENCES doctors(id),
    patient_id  TEXT NOT NULL REFERENCES patients(id),
    slot        TEXT NOT NULL,
    date        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'confirmed',
    UNIQUE(doctor_id, slot, date)
);

CREATE TABLE IF NOT EXISTS medical_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id   TEXT NOT NULL REFERENCES patients(id),
    doctor_name  TEXT NOT NULL,
    note         TEXT NOT NULL,
    date         TEXT NOT NULL
);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row       # lets us read rows like dicts: row["name"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the tables if they don't exist yet. Safe to call every time the app starts."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def reset_db():
    """Danger: wipes all data by deleting the database file. Useful during development."""
    conn = get_connection()
    conn.close()
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


if __name__ == "__main__":
    # Running: python database.py  ->  just (re)creates the tables.
    init_db()
    print(f"Database ready at: {DB_PATH}")
