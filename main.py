from PySide6.QtWidgets import QApplication
import sys


from app.core.config import VOSK_DIR, PIPER_DIR


def check_env():
    """
    Sprawdza, czy wszystkie krytyczne komponenty istnieją.
    Funkcja bazuje na pliku '/app/core/config.py'.
    """

    # Weryfikacja modeli
    if not VOSK_DIR.exists() or not any(VOSK_DIR.iterdir()):
        print(f"Brak modelu Vosk(STT) w {VOSK_DIR}!")

    if not PIPER_DIR.exists() or not any(PIPER_DIR.iterdir()):
        print(f"Brak modelu Piper(TTS) w {PIPER_DIR}!")

    # TODO: Sprawdzanie bazy danych


def main():
    print("==-URUCHAMIANIE-==")

    check_env()

    # Inicjalizacja PySide6
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    print("Ładowanie GUI")
    # TODO: GUI

    print("Aplikacja gotowa do działania!")
    sys.exit(app.exec()) # Event loop

if __name__ == "__main__":
    main()
