from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from app.ui.base_view import BaseView
from app.ui.skeleton_lobby_view import SkeletonLobbyView


class LobbyView(BaseView):
    """
    Klasa reprezentująca widok powitalny (Lobby) aplikacji.
    """

    def __init__(self):
        super().__init__(SkeletonLobbyView, "lobbyView")

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """
        Tworzenie elementów interfejsu.
        """
        self.title_label = QLabel("Ekran lobby")
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
