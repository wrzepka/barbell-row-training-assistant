from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from app.workers.camera_worker import CameraWorker
from app.workers.pose_worker import PoseWorker


class PoseCameraWidget(QWidget):
    """
    Samodzielny komponent UI (Widget) odpowiedzialny za wyświetlanie obrazu z pojedynczej kamery
    oraz nakładanie na niego szkieletu (MediaPipe).
    Zarządza własnymi wątkami w tle (CameraWorker, PoseWorker), nie blokując głównego interfejsu.
    """

    def __init__(self, camera_source, title_text):
        """
        Inicjalizuje widget kamery.

        :param camera_source: Indeks kamery (np. 0, 1) lub adres URL strumienia (np. DroidCam).
        :param title_text: Tekst wyświetlany nad podglądem wideo (np. "KAMERA 1").
        """

        super().__init__()
        self.camera_source = camera_source

        self._camera_worker: CameraWorker | None = None
        self._pose_worker: PoseWorker | None = None

        self._dying_workers = []

        self._setup_ui(title_text)

    def _setup_ui(self, title_text):
        """
        Tworzy i układa elementy wizualne wewnątrz tego widgetu.
        """

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Etykieta tytułowa (np. "KAMERA 1")
        self.title_label = QLabel(title_text)
        self.title_label.setAlignment(Qt.AlignCenter)

        # Ekran wideo
        self.video_label = QLabel()
        self.video_label.setObjectName("cameraSlot")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        layout.addWidget(self.title_label)
        layout.addWidget(self.video_label, stretch=1)

    def _show_frame(self, img: QImage):
        """
        Slot (odbiornik) wywoływany automatycznie za każdym razem, gdy PoseWorker
        zakończy analizę klatki i wyemituje sygnał 'frame_ready'.

        :param img: Przetworzona klatka (QImage) ze narysowanym szkieletem.
        """

        px = QPixmap.fromImage(img).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.video_label.setPixmap(px)

    def _clean_up_worker(self, worker):
        """
        Pomocnicza metoda sprzątająca. Odpala się automatycznie,
        gdy CameraWorker zakończy swoją pętlę i wyemituje sygnał 'finished'.
        """
        if worker in self._dying_workers:
            self._dying_workers.remove(worker)
        worker.deleteLater()

    def start_camera(self):
        """
        Inicjuje i uruchamia wątki w tle odpowiedzialne za pobieranie obrazu i analizę AI.
        Łączy sygnały między workerami a interfejsem graficznym.
        """

        if self._camera_worker is not None:
            return  # Już działa

        self._pose_worker = PoseWorker()
        self._pose_worker.frame_ready.connect(self._show_frame)
        self._pose_worker.start()

        self._camera_worker = CameraWorker(self.camera_source)
        self._camera_worker.frame_ready.connect(self._pose_worker.submit)
        self._camera_worker.start()

    def stop_camera(self):
        """
        Asynchroniczne zatrzymywanie kamer.
        Wyłącza kamery bez blokowania przełączania zakładek - odbywa się to poprzez _dying_workers:
        worek z referenacjami obiektów do usunięcia.
        """

        # Odłączamy połączenie sygnałów między workerami, aby nie były przesyłane kolejne klatki.
        if self._camera_worker:
            try:
                self._camera_worker.frame_ready.disconnect()
            except Exception:
                pass

        if self._pose_worker:
            try:
                self._pose_worker.frame_ready.disconnect()
            except Exception:
                pass

        # Bezpieczne wyłączanie
        if self._camera_worker:
            cw = self._camera_worker
            # Dodajemy camera workera do listy aby python nie usunął go z pamięci i spowodował crasha.
            self._dying_workers.append(cw)
            cw.stop()

            cw.finished.connect(lambda w=cw: self._clean_up_worker(w)) # Wyczyść obiekt
            self._camera_worker = None

        if self._pose_worker:
            pw = self._pose_worker

            # Dodajemy pose workera do listy aby python nie usunął go z pamięci i spowodował crasha.
            self._dying_workers.append(pw)
            pw.stop()
            pw.deleteLater()
            self._pose_worker = None
