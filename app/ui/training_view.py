from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class TrainingView(QWidget):
    """
    Widok treningowy wyświetlający podgląd z kamer.
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
        self.setObjectName("trainingView")

        # Wymuszenie obsługi QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _create_widgets(self):
        """
        Tworzenie elementów interfejsu.
        """
        self.title_label = QLabel("Ekran treningu")
        self.title_label.setObjectName("placeholderLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.cam_laptop = QLabel("KAMERA 1\n(Laptop)")
        self.cam_laptop.setObjectName("cameraSlot")
        self.cam_laptop.setAlignment(Qt.AlignCenter)

        self.cam_droid = QLabel("KAMERA 2\n(DroidCam)")
        self.cam_droid.setObjectName("cameraSlot")
        self.cam_droid.setAlignment(Qt.AlignCenter)

        self.stats_label = QLabel("Statystyki")
        self.stats_label.setObjectName("placeholderLabel")
        self.stats_label.setAlignment(Qt.AlignCenter)

    def _setup_layout(self):
        """
        Ustawienie rozmieszczenia kamer obok siebie.
        """
        # Główny układ
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Układ dla kamer
        cameras_layout = QHBoxLayout()
        cameras_layout.setSpacing(15)
        cameras_layout.addWidget(self.cam_laptop)
        cameras_layout.addWidget(self.cam_droid)

        main_layout.addWidget(self.title_label, stretch=1)
        main_layout.addLayout(cameras_layout, stretch=6)
        main_layout.addWidget(self.stats_label, stretch=1)
