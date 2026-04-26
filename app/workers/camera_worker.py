from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap
import cv2

FRAME_INTERVAL_MS = 33


class CameraWorker(QThread):
    """
    Wątek czytający klatki z jednej kamery i emitujący je do GUI.
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
