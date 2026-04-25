from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget
from app.ui.navbar import Navbar
from app.ui.lobby_view import LobbyView
from app.ui.training_view import TrainingView
from app.ui.history_view import HistoryView
from PySide6.QtCore import Qt


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
