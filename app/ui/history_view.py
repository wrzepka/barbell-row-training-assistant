from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class HistoryView(QWidget):
    """
    Klasa reprezentująca widok z historią treningów użytkownika.
    """

    def __init__(self):
        super().__init__()

        self._setup_view_settings()
        self._create_widgets()
        self._setup_layout()

    def _setup_view_settings(self):
        """
        Konfiguracja podstawowych parametrów widoku.
        """
        self.setObjectName("historyView")
        # Wymuszenie obsługi QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _create_widgets(self):
        """
        Tworzenie elementów interfejsu.
        """
        self.title_label = QLabel("Ekran historii")
        self.title_label.setObjectName("placeholderLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

    def _setup_layout(self):
        """
        Ustawienie rozmieszczenia elementów.
        """
        layout = QVBoxLayout(self)

        layout.addWidget(self.title_label)
        layout.addStretch()

        layout.setContentsMargins(10, 10, 10, 10)
