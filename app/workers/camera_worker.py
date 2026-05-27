from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
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
        self._running = False

    def run(self):
        backend = cv2.CAP_DSHOW if isinstance(self._index, int) else cv2.CAP_ANY
        cap = cv2.VideoCapture(self._index, backend)

        if not cap.isOpened():

            return


        for _ in range(30):
            ok, frame = cap.read()
            if ok:
                break
        else:
            cap.release()
            return

        self._running = True

        while self._running:
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
            self.frame_ready.emit(img)

        cap.release()

    def stop(self):
        self._running = False
        self.quit()