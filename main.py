from PySide6.QtWidgets import QApplication
import sys
from app.core.config import VOSK_DIR, PIPER_DIR, STYLE_QSS_FILE, UI_DIR, LOADING_IMAGE
from app.ui.loading_screen import LoadingScreen
from app.ui.main_window import MainWindow


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
    # Weryfikacja głównego pliku styli dla PySide6
    if not STYLE_QSS_FILE.exists():
        print(f"Brak pliku globalnych styli GUI w {UI_DIR}")

    # TODO: Sprawdzanie bazy danych


def main():
    print("==-URUCHAMIANIE-==")

    check_env()

    # Inicjalizacja PySide6
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Otworzenie globalnych styli
    with open(STYLE_QSS_FILE, "r", encoding="utf-8") as style_file:
        app.setStyleSheet(style_file.read())

    # uruchomienie loading screenu
    loading_screen = LoadingScreen(LOADING_IMAGE)
    loading_screen.show()

    print("Ładowanie GUI")
    window = MainWindow()

    def on_ready():
        window.showMaximized()
        loading_screen.close()

    # czekanie na emisje sygnału, reprezentujący koniec inicjacji modeli.
    # wywołuje on_ready(), która wyłącza loading screen i pokazuje główne okno apki.
    window.initialization_complete.connect(on_ready)

    print("Aplikacja gotowa do działania!")
    sys.exit(app.exec())  # Event loop



if __name__ == "__main__":
    main()
