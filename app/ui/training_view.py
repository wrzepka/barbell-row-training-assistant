from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy, QStackedWidget
from PySide6.QtCore import Qt, QTimer

from app.const import ScreenModes
from app.ui.base_view import BaseView
from app.ui.pose_camera import PoseCameraWidget
from app.ui.skeleton_training_view import SkeletonTrainingView

#Kamerka internetowa
#TODO: ogarnać sposób na dobre szukanie indeksów kamer
LAPTOP_CAM_INDEX = 0
#droidcam chwilowe rozwiazanie bo duzy delay
DROIDCAM_INDEX   = "http://192.168.0.83:4747/video"

class TrainingView(BaseView):
    """
    Widok treningowy z podglądem z dwóch kamer i szkieletem MediaPipe.
    """

    def __init__(self):
        super().__init__(SkeletonTrainingView, "trainingView")

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """
        Inicjalizacja i konfiguracja wszystkich elementów interfejsu (widgetów),
        z których składa się ten widok, bez ustalania ich ostatecznego położenia.
        """

        self.title_label = QLabel("Ekran treningu")
        self.title_label.setObjectName("placeholderLabel")
        self.title_label.setAlignment(Qt.AlignCenter)

        self.cam_laptop = PoseCameraWidget(LAPTOP_CAM_INDEX, "KAMERA 1\n(Laptop)")
        self.cam_droid = PoseCameraWidget(DROIDCAM_INDEX, "KAMERA 2\n(DroidCam)")

        self.stats_label = QLabel("Statystyki")
        self.stats_label.setObjectName("placeholderLabel")
        self.stats_label.setAlignment(Qt.AlignCenter)

    def _setup_layout(self):
        """
        Układa wcześniej utworzone widgety w odpowiedniej strukturze (Layout).
        Wykorzystuje układ pionowy (VBox) dla całego ekranu, wewnątrz którego
        zagnieżdżony jest układ poziomy (HBox) dla zestawienia kamer obok siebie.
        """

        main_layout = QVBoxLayout(self.content_page)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Układ dla kamer
        cameras_layout = QHBoxLayout()
        cameras_layout.setSpacing(15)
        cameras_layout.addWidget(self.cam_laptop)
        cameras_layout.addWidget(self.cam_droid)

        main_layout.addWidget(self.title_label,  stretch=1)
        main_layout.addLayout(cameras_layout,    stretch=6)
        main_layout.addWidget(self.stats_label,  stretch=1)

    def showEvent(self, event):
        """
        Metoda wywoływana automatycznie przez Qt, gdy widget staje się widoczny
        (np. po przełączeniu na tę zakładkę w QStackedWidget).
        Uruchamia pobieranie obrazu i analizę AI tylko wtedy, gdy użytkownik faktycznie na to patrzy.
        """
        self.cam_laptop.start_camera()
        self.cam_droid.start_camera()

        super().showEvent(event)

    def hideEvent(self, event):
        """
        Metoda wywoływana automatycznie przez Qt, gdy widget zostaje ukryty
        (np. przy przejściu do innej zakładki, jak Historia lub Lobby).
        Zatrzymuje kamery i zwalnia zasoby sprzętowe, aby aplikacja działała płynnie w tle.
        """

        super().hideEvent(event)
        self.cam_laptop.stop_camera()
        self.cam_droid.stop_camera()

    def closeEvent(self, event):
        """
        Metoda wywoływana automatycznie przy całkowitym niszczeniu widgetu
        (np. podczas wyłączania całej aplikacji).
        Zapewnia twarde zatrzymanie procesów sprzętowych i zapobiega błędom (tzw. memory leaks).
        """

        self.cam_laptop.stop_camera()
        self.cam_droid.stop_camera()
        super().closeEvent(event)