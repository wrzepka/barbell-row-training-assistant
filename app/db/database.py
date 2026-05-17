# Zawartość pliku: db/database.py
import sqlite3
from datetime import datetime
from pathlib import Path

# Ścieżka wskazująca na plik training.db w tym samym folderze (db/)
DB_PATH = Path(__file__).parent / "training.db"


def create_database():
    """Tworzy bazę danych oraz tabelę historii treningów, jeśli jeszcze nie istnieją."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Tworzymy tabelę z pełnymi parametrami odpowiadającymi widokowi GUI
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
            to_fix TEXT NOT NULL
        )
    """
    )
    connection.commit()
    connection.close()


def add_training_entry(weight, reps, sets, duration, score, to_fix_list):
    """Dodaje nowy rekord treningowy do bazy danych."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Formatujemy aktualny czas (np. 2026-05-17 18:30)
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Zamieniamy listę uwag na jeden ciąg tekstowy połączony średnikami
    to_fix_string = ";".join(to_fix_list) if to_fix_list else "Brak uwag"

    cursor.execute(
        """
        INSERT INTO training_history (date, weight, reps, sets, duration, score, to_fix) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (current_date, weight, reps, sets, duration, score, to_fix_string),
    )
    connection.commit()
    connection.close()


def get_training_statistics():
    """Pobiera wszystkie rekordy posortowane od najnowszego treningu (dla listy i statystyk)."""
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT date, weight, reps, sets, duration, score, to_fix 
        FROM training_history 
        ORDER BY date DESC
        """
    )
    rows = cursor.fetchall()
    connection.close()

    # Mapujemy surowe wiersze z bazy danych na listę słowników (zgodną z formatem MOCK_DATA)
    history_data = []
    for row in rows:
        # Rozbijamy ciąg tekstowy z uwagami z powrotem na listę w Pythonie
        to_fix_list = row[6].split(";") if row[6] else ["Brak uwag"]

        history_data.append({
            "date": row[0],
            "weight": f"{row[1]}kg" if isinstance(row[1], (int, float)) else str(row[1]),
            "reps": str(row[2]),
            "sets": row[3],
            "duration": row[4],
            "score": row[5],
            "to_fix": to_fix_list
        })

    return history_data