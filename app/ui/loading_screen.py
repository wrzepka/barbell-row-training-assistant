from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class LoadingScreen(QWidget):
    """
    Klasa reprezentująca okno ładowania (splash screen).
    Wyświetla logo, informację tekstową oraz animowany pasek postępu.
    """

    def __init__(self, image_path: str):
        """
        Inicjalizuje ekran ładowania.

        Args:
            image_path (str): Ścieżka do pliku graficznego (logo/sprite).
        """
        super().__init__()

        self.image_path = image_path
        self._setup_view_settings()
        self._create_widgets()
        self._setup_layout()

    def _setup_view_settings(self):
        """
        Konfiguruje techniczne parametry okna systemowego.
        Usuwa ramki, wymusza widoczność na wierzchu i przygotowuje do stylowania QSS.
        """
        # FramelessWindowHint: usuwa pasek tytułowy i systemowe przyciski (X, min, max)
        # WindowStaysOnTopHint: sprawia, że okno nie chowa się pod inne aplikacje
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        self.setObjectName("loadingScreen")
        # Wymuszenie nadpisania tła okna przez styl QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Wymuszenie stałej wielkości okna
        self.setFixedSize(600, 400)

    def _create_widgets(self):
        """
        Instancjonuje i konfiguruje poszczególne elementy interfejsu (Logo, Tekst, Pasek).
        """
        # konfiguracja sprite'a
        self.image_label = QLabel()
        self.image_label.setObjectName("loadingLogo")
        self.image_label.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap(self.image_path)
        self.image_label.setPixmap(
            pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # konfiguracja labela/tekstu poniżej sprite'a
        self.info_label = QLabel("Inicjalizacja modeli AI...\nProszę czekać.")
        self.info_label.setObjectName("loadingInfo")
        self.info_label.setAlignment(Qt.AlignCenter)

        # konfiguracja paska postępu
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("loadingProgress")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)

    def _setup_layout(self):
        """
        Definiuje układ elementów w oknie i zarządza przestrzenią (marginesy, odstępy).
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        layout.addWidget(self.image_label, stretch=1)
        layout.addWidget(self.info_label)
        layout.addWidget(self.progress_bar)
