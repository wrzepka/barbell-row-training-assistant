from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup, QLabel
from PySide6.QtCore import Qt, Signal
from app.const import Screen


class Navbar(QWidget):
    """
    Klasa reprezentująca górny pasek nawigacyjny aplikacji.
    """
    LOGO_SIZE = 150
    NAVBAR_HEIGHT = 60
    button_clicked = Signal(int)

    def __init__(self, image_path: str):
        super().__init__()

        self.image_path = image_path
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
        self.setFixedHeight(self.NAVBAR_HEIGHT)

        # Wymuszenie nadpisania tła okna przez styl QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _build_ui(self):
        """
        Tworzy przyciski oraz logo i układa je w layoucie.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)

        self.image_label = self._create_logo()
        self.nav_buttons = {
            Screen.LOBBY: self._create_nav_button("LOBBY", Screen.LOBBY),
            Screen.TRAINING: self._create_nav_button("TRENING", Screen.TRAINING),
            Screen.HISTORY: self._create_nav_button("HISTORIA", Screen.HISTORY),
        }

        layout.addWidget(self.image_label)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        for btn in self.nav_buttons.values():
            buttons_layout.addWidget(btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)
        layout.addSpacing(self.LOGO_SIZE) # skontrowanie loga z drugiej strony (dzięki temu guziki są idealnie wycentrowane)

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

    def _create_logo(self):
        """
        Tworzy konfiguruje obiekt z logiem aplikacji.
        :return: obiekt QLabel z logiem aplikacji
        """

        logo_label = QLabel()
        logo_label.setObjectName("Logo")
        logo_label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.LOGO_SIZE, self.LOGO_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
        else:
            print(f"Błąd! Brak loga w: {self.image_path}")

        return logo_label