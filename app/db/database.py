# Zawartość pliku: app/db/database.py
import sqlite3
import json
from datetime import datetime
from app.core.config import DB_PATH


def create_database():
    """Tworzy bazę danych oraz tabelę historii treningów, jeśli jeszcze nie istnieją."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS training_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            weight REAL NOT NULL,
            reps INTEGER NOT NULL,
            sets INTEGER NOT NULL,
            duration TEXT NOT NULL,
            score INTEGER NOT NULL,
            to_fix TEXT NOT NULL,
            sets_detail TEXT NOT NULL DEFAULT '[]'
        )
    """
    )

    # Migracja: dodaj kolumnę sets_detail jeśli jeszcze nie istnieje (stara baza)
    try:
        cursor.execute("ALTER TABLE training_history ADD COLUMN sets_detail TEXT NOT NULL DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass  # kolumna już istnieje

    connection.commit()
    connection.close()


def add_training_entry(weight, reps, sets, duration, score, to_fix_list, sets_detail=None):
    """
    Dodaje nowy rekord treningowy do bazy danych.

    sets_detail – lista słowników z danymi per-seria:
        [{"set_nr": 1, "reps": 10, "weight": 65.0}, ...]
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    to_fix_string = ";".join(to_fix_list) if to_fix_list else "Brak uwag"
    sets_detail_json = json.dumps(sets_detail or [], ensure_ascii=False)

    cursor.execute(
        """
        INSERT INTO training_history (date, weight, reps, sets, duration, score, to_fix, sets_detail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (current_date, weight, reps, sets, duration, score, to_fix_string, sets_detail_json),
    )
    connection.commit()
    connection.close()


def get_training_statistics():
    """Pobiera wszystkie rekordy posortowane od najnowszego treningu."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT date, weight, reps, sets, duration, score, to_fix, sets_detail
        FROM training_history
        ORDER BY date DESC
        """
    )
    rows = cursor.fetchall()
    connection.close()

    history_data = []
    for row in rows:
        to_fix_list = row[6].split(";") if row[6] else ["Brak uwag"]

        try:
            sets_detail = json.loads(row[7]) if row[7] else []
        except (json.JSONDecodeError, TypeError):
            sets_detail = []

        history_data.append({
            "date": row[0],
            "weight": f"{row[1]:.1f} kg" if isinstance(row[1], (int, float)) else str(row[1]),
            "reps": str(row[2]),
            "sets": row[3],
            "duration": row[4],
            "score": row[5],
            "to_fix": to_fix_list,
            "sets_detail": sets_detail,
        })

    return history_data