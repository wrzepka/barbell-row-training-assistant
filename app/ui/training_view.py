from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap
import cv2



LAPTOP_CAM_INDEX  = 1
#chwilowe rozwiązanie, ponieważ jest bardzo duży delay na kamerze z droidcam
DROIDCAM_INDEX    = "http://192.168.100.123:4747/video"

FRAME_INTERVAL_MS = 33


class CameraWorker(QThread):
    """
    Wątek czytający klatki z jednej kamery i emitujący je do GUI.
    Używa self.exec() + QTimer zamiast busy-loop — stabilne na Windows.
    """

    frame_ready = Signal(QImage)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self._index = index

    def run(self):
        backend = cv2.CAP_DSHOW if isinstance(self._index, int) else cv2.CAP_ANY
        cap = cv2.VideoCapture(self._index, backend)
        if not cap.isOpened():
            return

        timer = QTimer()
        timer.setInterval(FRAME_INTERVAL_MS)

        def read_frame():
            ok, frame = cap.read()
            if not ok:
                timer.stop()
                return
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
            self.frame_ready.emit(img)

        timer.timeout.connect(read_frame)
        timer.start()

        self.exec()
        timer.stop()
        cap.release()

    def stop(self):
        self.quit()
        self.wait(3000)


class TrainingView(QWidget):
    """
    Widok treningowy wyświetlający podgląd z kamer.
    """

    def __init__(self):
        super().__init__()

        self._worker_laptop: CameraWorker | None = None
        self._worker_droid:  CameraWorker | None = None

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
        # Zablokowanie rozszerzania — kamera zostaje w swoim miejscu
        self.cam_laptop.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self.cam_droid = QLabel("KAMERA 2\n(DroidCam)")
        self.cam_droid.setObjectName("cameraSlot")
        self.cam_droid.setAlignment(Qt.AlignCenter)
        self.cam_droid.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

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


    def _show_frame(self, label: QLabel, img: QImage):
        px = QPixmap.fromImage(img).scaled(
            label.width(),
            label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        label.setPixmap(px)

    def _start_cameras(self):
        self._worker_laptop = CameraWorker(LAPTOP_CAM_INDEX)
        self._worker_laptop.frame_ready.connect(
            lambda img: self._show_frame(self.cam_laptop, img)
        )
        self._worker_laptop.start()

        self._worker_droid = CameraWorker(DROIDCAM_INDEX)
        self._worker_droid.frame_ready.connect(
            lambda img: self._show_frame(self.cam_droid, img)
        )
        self._worker_droid.start()

    def _stop_cameras(self):
        for attr in ("_worker_laptop", "_worker_droid"):
            worker = getattr(self, attr, None)
            if worker:
                worker.stop()
            setattr(self, attr, None)

    def showEvent(self, event):
        super().showEvent(event)
        self._start_cameras()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._stop_cameras()