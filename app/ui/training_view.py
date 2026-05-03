from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from app.workers.camera_worker import CameraWorker
from app.workers.pose_worker import PoseWorker

#Kamerka internetowa
LAPTOP_CAM_INDEX = 1
#droidcam chwilowe rozwiazanie bo duzy delay
DROIDCAM_INDEX   = "http://192.168.0.83:4747/video"


class TrainingView(QWidget):
    """
    Widok treningowy z podglądem z dwóch kamer i szkieletem MediaPipe.
    Przetwarzanie pose odbywa się w tle (PoseWorker) — UI nie jest blokowane.
    """

    def __init__(self):
        super().__init__()

        self._worker_laptop: CameraWorker | None = None
        self._worker_droid:  CameraWorker | None = None
        self._pose_laptop:   PoseWorker   | None = None
        self._pose_droid:    PoseWorker   | None = None

        self._setup_view_settings()
        self._create_widgets()
        self._setup_layout()

    def _setup_view_settings(self):
        """
                Konfiguracja podstawowych parametrów widoku.
        """
        self.setObjectName("trainingView")
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
        # Zablokowanie rozszerzania — kamera zostaje w swoim miejscu
        self.cam_laptop.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self.cam_droid = QLabel("KAMERA 2\n(DroidCam)")
        self.cam_droid.setObjectName("cameraSlot")
        self.cam_droid.setAlignment(Qt.AlignCenter)
        # Zablokowanie rozszerzania — kamera zostaje w swoim miejscu
        self.cam_droid.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self.stats_label = QLabel("Statystyki")
        self.stats_label.setObjectName("placeholderLabel")
        self.stats_label.setAlignment(Qt.AlignCenter)

    def _setup_layout(self):
        """
        Ustawienie rozmieszczenia kamer obok siebie.
        """
        main_layout = QVBoxLayout(self)
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

    def _show_frame(self, label: QLabel, img: QImage):
        px = QPixmap.fromImage(img).scaled(
            label.width(),
            label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        label.setPixmap(px)

    def _start_cameras(self):
        # --- kamera laptopa ---
        self._pose_laptop = PoseWorker()
        self._pose_laptop.frame_ready.connect(
            lambda img: self._show_frame(self.cam_laptop, img)
        )
        self._pose_laptop.start()

        self._worker_laptop = CameraWorker(LAPTOP_CAM_INDEX)
        self._worker_laptop.frame_ready.connect(self._pose_laptop.submit)
        self._worker_laptop.start()

        # --- DroidCam ---
        self._pose_droid = PoseWorker()
        self._pose_droid.frame_ready.connect(
            lambda img: self._show_frame(self.cam_droid, img)
        )
        self._pose_droid.start()

        self._worker_droid = CameraWorker(DROIDCAM_INDEX)
        self._worker_droid.frame_ready.connect(self._pose_droid.submit)
        self._worker_droid.start()

    def _stop_cameras(self):
        for cam_attr, pose_attr in (
            ("_worker_laptop", "_pose_laptop"),
            ("_worker_droid",  "_pose_droid"),
        ):
            worker = getattr(self, cam_attr, None)
            if worker:
                worker.stop()
            setattr(self, cam_attr, None)

            processor = getattr(self, pose_attr, None)
            if processor:
                processor.stop()
            setattr(self, pose_attr, None)

    def showEvent(self, event):
        super().showEvent(event)
        self._start_cameras()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._stop_cameras()

    def closeEvent(self, event):
        self._stop_cameras()
        super().closeEvent(event)