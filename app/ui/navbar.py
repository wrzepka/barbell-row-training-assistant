from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, Signal
from app.const import Screen


class Navbar(QWidget):
    """
    Klasa reprezentująca górny pasek nawigacyjny aplikacji.
    """

    button_clicked = Signal(int)

    def __init__(self):
        super().__init__()

        self._init_logic()
        self._setup_style()
        self._build_ui()
        self.set_active_tab(Screen.LOBBY)

    def _init_logic(self):
        """
        Inicjalizuje mechanizmy sterowania bez dotykania UI.
        """
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.group.idClicked.connect(self.button_clicked.emit)

    def _setup_style(self):
        """
        Konfiguruje parametry techniczne i wizualne paska.
        """
        self.setObjectName("navBar")
        self.setFixedHeight(60)

        # Wymuszenie obsługi QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _build_ui(self):
        """
        Tworzy przyciski i układa je w layoucie.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)

        self.nav_buttons = {
            Screen.LOBBY: self._create_nav_button("LOBBY", Screen.LOBBY),
            Screen.TRAINING: self._create_nav_button("TRENING", Screen.TRAINING),
            Screen.HISTORY: self._create_nav_button("HISTORIA", Screen.HISTORY),
        }

        layout.addStretch()
        for btn in self.nav_buttons.values():
            layout.addWidget(btn)
        layout.addStretch()

    def _create_nav_button(self, text, screen_id: Screen):
        """
        Fabryka przycisków przypisująca je od razu do grupy z odpowiednim ID.
        """
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)

        self.group.addButton(btn, screen_id.value)
        return btn

    def set_active_tab(self, screen_id: Screen):
        """
        Zmienia aktywny przycisk/widok programowo.
        """
        if screen_id in self.nav_buttons:
            self.nav_buttons[screen_id].setChecked(True)
