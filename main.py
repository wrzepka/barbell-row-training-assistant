import ctypes
import sys

from PySide6.QtWidgets import QApplication
from app.core.config import VOSK_DIR, PIPER_DIR, STYLE_QSS_FILE, UI_DIR, LOGO_WITHOUT_BG
from app.ui.loading_screen import LoadingScreen
from app.ui.main_window import MainWindow

from app.db.database import create_database, add_training_entry, get_training_statistics


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

    # Inicjalizacja bazy danych w folderze db/
    print("Inicjalizacja bazy danych...")
    create_database()

    # Jeśli baza danych jest świeża i pusta, wrzucamy kilka rekordów startowych do testu
    if not get_training_statistics():
        print("Baza danych jest pusta. Generowanie wpisów historycznych...")
        add_training_entry(50.0, 10, 3, "18 min", 87, ["Brak uwag"])
        add_training_entry(55.0, 10, 3, "19 min", 75, ["Prowadź łokcie bliżej ciała"])
        add_training_entry(60.0, 10, 4, "22 min", 65, ["Wyprostuj plecy!", "Zwolnij ruch"])
        add_training_entry(60.0, 12, 3, "18 min", 95, ["Brak uwag"])


def main():
    print("==-URUCHAMIANIE-==")

    check_env()

    # Umożliwienie wyświetlania loga w pasku zadań w Windows
    if sys.platform == "win32":
        my_app_id = "pl.kck.barbellrowassistant.v0.4"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

    # Inicjalizacja PySide6
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Otworzenie globalnych styli
    with open(STYLE_QSS_FILE, "r", encoding="utf-8") as style_file:
        app.setStyleSheet(style_file.read())

    # uruchomienie loading screenu
    loading_screen = LoadingScreen(LOGO_WITHOUT_BG)
    loading_screen.show()

    print("Ładowanie GUI")
    window = MainWindow()

    def on_ready():
        window.showMaximized()
        loading_screen.close()

    # czekanie na emisje sygnału, reprezentujący koniec inicjacji modeli.
    window.initialization_complete.connect(on_ready)

    print("Aplikacja gotowa do działania!")
    sys.exit(app.exec())  # Event loop


if __name__ == "__main__":
    main()