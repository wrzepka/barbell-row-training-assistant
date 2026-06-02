from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget

from app.core.config import LOGO_WITHOUT_BG, LOGO_ICON
from app.ui.navbar import Navbar
from app.ui.lobby_view import LobbyView
from app.ui.training_view import TrainingView
from app.ui.history_view import HistoryView
from PySide6.QtCore import Qt, Signal, QTimer

from app.core.voice_manager import VoiceManager

class MainWindow(QMainWindow):
    """
    Główne okno aplikacji zarządzające nawigacją i wyświetlaniem poszczególnych modułów.
    """

    initialization_complete = Signal()

    def __init__(self):
        super().__init__()

        self._setup_window_settings()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

        # start modeli - z 300 ms opóźnienia, aby umożliwić narysowanie loading screenu.
        QTimer.singleShot(300, self._init_voice_manager)


    def _setup_window_settings(self):
        """
        Konfiguruje parametry techniczne głównego okna i kontenera centralnego.
        """
        self.setWindowTitle("Barbell Row Assistant 0.4.0")
        self.setWindowIcon(QIcon(str(LOGO_ICON)))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setObjectName("mainContainer")

        # Wymuszenie nadpisania tła okna przez styl QSS
        self.central_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _create_widgets(self):
        """
        Instancjonuje główne komponenty interfejsu.
        """
        self.navbar = Navbar(LOGO_WITHOUT_BG)

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

    def _init_voice_manager(self):
        """
        Tworzy instancję menedżera i podpina nasłuch komend głosowych.
        Nam sam koniec emituje sygnał `initialization_complete`,
        który jest nasłuchiwany w `main.py` - kończy wyświetlanie loading'u
        """
        self.voice_manager = VoiceManager(parent=self)
        self.voice_manager.command_recognized.connect(self._handle_voice_commands)

        self.voice_manager.speak("System gotowy do działania.")
        self.initialization_complete.emit() # emisja sygnału, oznaczającego koniec ładowania modeli.

    def _handle_voice_commands(self, text: str):
        """
        Tutaj trafia rozpoznany tekst z mikrofonu.
        """
        print(f"[{text}]")

        # Można uprościć kod tutaj bazując na sygnałach, które będą przechwtywane w VoiceManager
        # przykładowa logika reagowania na komendy
        if "trening" in text.lower() or "terenie" in text.lower() or "trendy" in text.lower() or "rynek" in text.lower() or "premier" in text.lower() or "trend" in text.lower() or "teren" in text.lower():
            self.switch_page(1)  #przełącza na trening
            self.voice_manager.speak("Przechodzę do treningu.")

        elif "historia" in text.lower() or "historie" in text.lower() or "zdrowia" in text.lower() or "historię" in text.lower():
            self.switch_page(2)  #przełącza na historie
            self.voice_manager.speak("Oto twoja historia treningów.")
        elif "lobby" in text.lower() or "start" in text.lower() or "po lody" in text.lower() or "loty" in text.lower() or "lampki" in text.lower() or "lotu" in text.lower() or "lody" in text.lower() or "robi" in text.lower() or "nowi" in text.lower() or "logiki" in text.lower() or "roku" in text.lower() or "nowy" in text.lower() or "lobbing" in text.lower() or "nogi" in text.lower() or "lubi" in text.lower() or "lampy" in text.lower() or "login" in text.lower() or "lori" in text.lower() or "wątpie" in text.lower() or "lot" in text.lower() or "stan" in text.lower():
            self.switch_page(0) #przełąccza na start
            self.voice_manager.speak("Przechodzę na stronę startową")

    def closeEvent(self, event):
        """
        Zapewnia bezpieczne wyłączenie procesów przy zamykaniu okna.
        """
        if hasattr(self, 'voice_manager'):
            self.voice_manager.stop_all()

        super().closeEvent(event)