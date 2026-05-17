import sqlite3
from datetime import datetime


def stworz_baze():
    polaczenie = sqlite3.connect("trening.db")
    kursor = polaczenie.cursor()
    kursor.execute(
        """
        CREATE TABLE IF NOT EXISTS statystyki (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            ciezar REAL NOT NULL,
            powtorzenia INTEGER NOT NULL
        )
    """
    )
    polaczenie.commit()
    polaczenie.close()


def dodaj_wpis(ciezar, powtorzenia):
    polaczenie = sqlite3.connect("trening.db")
    kursor = polaczenie.cursor()

    dzisiejsza_data = datetime.now().strftime("%Y-%m-%d")

    kursor.execute(
        "INSERT INTO statystyki (data, ciezar, powtorzenia) VALUES (?, ?, ?)",
        (dzisiejsza_data, ciezar, powtorzenia),
    )
    polaczenie.commit()
    polaczenie.close()


def pobierz_statystyki():
    polaczenie = sqlite3.connect("trening.db")
    kursor = polaczenie.cursor()
    kursor.execute(
        "SELECT data, ciezar, powtorzenia FROM statystyki ORDER BY data ASC"
    )
    wyniki = kursor.fetchall()
    polaczenie.close()
    return wyniki


stworz_baze()

dodaj_wpis(85.0, 5)
dodaj_wpis(87.5, 4)

wszystkie_wpisy = pobierz_statystyki()

print("--- TWOJE STATYSTYKI ---")
for wpis in wszystkie_wpisy:
    data, ciezar, powtorzenia = wpis
    print(f"Data: {data} | Ciężar: {ciezar} kg | Powtórzenia: {powtorzenia}")