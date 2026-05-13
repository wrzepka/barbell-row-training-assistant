from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget
from PySide6.QtCore import Qt, QTimer

from app.const import ScreenModes
from app.ui.skeleton_history_view import SkeletonHistoryView


class HistoryView(QWidget):
    """
    Klasa reprezentująca widok z historią treningów użytkownika.
    """

    def __init__(self):
        super().__init__()

        self._setup_view_settings()
        self._create_widgets()
        self._setup_stack()
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
        layout = QVBoxLayout(self.content_page)

        layout.addWidget(self.title_label)
        layout.addStretch()

        layout.setContentsMargins(10, 10, 10, 10)

    # TODO: zrefaktoryzować do klasy bazowej: dwie metody powtarzają się
    def _setup_stack(self):
        """
        Tworzy QStackedWidget i definiuje dwie strony: szkielet oraz właściwy interfejs.
        """

        self.main_stack = QStackedWidget(self)
        self.skeleton_page = SkeletonHistoryView()
        self.content_page = QWidget()

        self.main_stack.addWidget(self.skeleton_page)  # Index 0
        self.main_stack.addWidget(self.content_page)  # Index 1

        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.addWidget(self.main_stack)

    def activate_real_ui(self):
        """
        Publiczna metoda do przełączenia widoku ze szkieletu na ten z realną zawartością.
        """

        self.main_stack.setCurrentIndex(ScreenModes.REAL)

    def showEvent(self, event):
        super().showEvent(event)
        self.main_stack.setCurrentIndex(ScreenModes.SKELETON)

        # udawanie pobierania danych - sztuczny delay - do wyrzucenia w przyszłości (TODO)
        QTimer.singleShot(1500, self.activate_real_ui)