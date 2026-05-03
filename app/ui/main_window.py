from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from app.ui.navbar import Navbar
from app.ui.lobby_view import LobbyView
from app.ui.training_view import TrainingView
from app.ui.history_view import HistoryView
from PySide6.QtCore import Qt

#import stt i tts
import piper
from app.core.config import PIPER_MODEL_FILE
from app.workers.stt_worker import STTWorker
from app.workers.tts_worker import TTSWorker


class MainWindow(QMainWindow):
    """
    Główne okno aplikacji zarządzające nawigacją i wyświetlaniem poszczególnych modułów.
    """

    def __init__(self):
        super().__init__()

        self._setup_window_settings()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        #start modeli
        self._init_voice_assistants()

    def _setup_window_settings(self):
        """
        Konfiguruje parametry techniczne głównego okna i kontenera centralnego.
        """
        self.setWindowTitle("Asystent wiosłowania sztangą ver.0.1.0")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setObjectName("mainContainer")

        # Wymuszenie obsługi QSS
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _create_widgets(self):
        """
        Instancjonuje główne komponenty interfejsu.
        """
        self.navbar = Navbar()

        # Menadżer ekranów i dodawanie widoków
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(LobbyView())  # 0
        self.stacked_widget.addWidget(TrainingView())  # 1
        self.stacked_widget.addWidget(HistoryView())  # 2

    def _setup_layout(self):
        """
        Definiuje rozmieszczenie komponentów w oknie głównym.
        """
        main_layout = QVBoxLayout(self.central_widget)

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.navbar)
        main_layout.addWidget(self.stacked_widget)

    def _connect_signals(self):
        """
        Rejestruje połączenia między sygnałami komponentów a ich działaniem (Slotami).
        """
        self.navbar.button_clicked.connect(self.switch_page)

    def switch_page(self, index):
        """
        Metoda zapewniająca pełną synchronizację z panelem nawigacyjnym przy zmianie widoków.
        """
        self.stacked_widget.setCurrentIndex(index)
        self.navbar.set_active_tab(index)

    def _init_voice_assistants(self):
        """
        Uruchamia instancje sztucznej inteligencji działające w tle.
        """
        try:
            # Ładowanie modelu Piper (raz dla całej aplikacji)
            model_path = f"{PIPER_MODEL_FILE}.onnx"
            print(f"🔊 Ładowanie modelu TTS z: {model_path}")

            voice = piper.PiperVoice.load(model_path)

            # Przekazujemy załadowany model do TTSWorker
            self.tts_worker = TTSWorker(voice)

        except Exception as e:
            print(f"❌ Błąd inicjalizacji TTS: {e}")
            self.tts_worker = None

        # Inicjalizacja STT
        self.stt_worker = STTWorker()
        self.stt_worker.text_recognized.connect(self._handle_voice_commands)
        self.stt_worker.start()

        # Powitanie, jeśli TTS działa
        if self.tts_worker:
            self.tts_worker.speak("System gotowy do działania.")

    def _handle_voice_commands(self, text: str):
        """
        Tutaj trafia rozpoznany tekst z mikrofonu.
        """
        print(f"[{text}]")

        # przykładowa logika reagowania na komendy
        if "trening" in text.lower():
            self.switch_page(1)  #przełącza na trening
            self.tts_worker.speak("Przechodzę do treningu.")

        elif "historia" in text.lower() or "historie" in text.lower():
            self.switch_page(2)  #przełącza na historie
            self.tts_worker.speak("Oto twoja historia treningów.")
        elif "lobby" in text.lower() or "start" in text.lower():
            self.switch_page(0) #przełąccza na start
            self.tts_worker.speak("Przechodzę na stronę startową")

    def closeEvent(self, event):
        """
        Zapewnia bezpieczne wyłączenie procesów przy zamykaniu okna.
        """
        self.stt_worker.stop()
        super().closeEvent(event)