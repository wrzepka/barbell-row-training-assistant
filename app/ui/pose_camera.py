from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap

from app.workers.camera_worker import CameraWorker
from app.workers.pose_worker import PoseWorker


class PoseCameraWidget(QWidget):
    """
    Samodzielny komponent UI odpowiedzialny za wyświetlanie obrazu z pojedynczej kamery
    oraz nakładanie na niego szkieletu (MediaPipe).

    Sygnały
    -------
    landmarks_ready(object)
        Przekazuje landmarki z PoseWorker dalej — do AnalysisWorker.
        Podpinaj zewnętrznie zależnie od roli kamery (boczna/przednia).
    """

    landmarks_ready = Signal(object)

    def __init__(self, camera_source, title_text):
        """
        :param camera_source: Indeks kamery (np. 0, 1) lub adres URL strumienia.
        :param title_text: Tekst wyświetlany nad podglądem wideo.
        """
        super().__init__()
        self.camera_source = camera_source

        self._camera_worker: CameraWorker | None = None
        self._pose_worker: PoseWorker | None = None
        self._dying_workers = []

        self._setup_ui(title_text)

    def _setup_ui(self, title_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title_text)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.video_label = QLabel()
        self.video_label.setObjectName("cameraSlot")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        layout.addWidget(self.title_label)
        layout.addWidget(self.video_label, stretch=1)

    def _show_frame(self, img: QImage):
        px = QPixmap.fromImage(img).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.video_label.setPixmap(px)

    def _clean_up_worker(self, worker):
        if worker in self._dying_workers:
            self._dying_workers.remove(worker)
        worker.deleteLater()

    def start_camera(self):
        if self._camera_worker is not None:
            return

        print(f"[DEBUG] start_camera: source={self.camera_source}")

        self._pose_worker = PoseWorker()
        self._pose_worker.frame_ready.connect(self._show_frame)
        self._pose_worker.landmarks_ready.connect(self.landmarks_ready)
        self._pose_worker.start()

        self._camera_worker = CameraWorker(self.camera_source)
        self._camera_worker.frame_ready.connect(self._pose_worker.submit)
        self._camera_worker.start()

        print(f"[DEBUG] workers started")

    def stop_camera(self):
        if self._camera_worker:
            try:
                self._camera_worker.frame_ready.disconnect()
            except Exception:
                pass

        if self._pose_worker:
            try:
                self._pose_worker.frame_ready.disconnect()
                self._pose_worker.landmarks_ready.disconnect()
            except Exception:
                pass

        if self._camera_worker:
            cw = self._camera_worker
            self._dying_workers.append(cw)
            cw.stop()
            cw.finished.connect(lambda w=cw: self._clean_up_worker(w))
            self._camera_worker = None

        if self._pose_worker:
            pw = self._pose_worker
            self._dying_workers.append(pw)
            pw.stop()
            pw.deleteLater()
            self._pose_worker = None