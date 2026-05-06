from __future__ import annotations

from queue import Queue, Empty
from threading import Thread

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# MediaPipe – obsługa różnych wersji pakietu
# ---------------------------------------------------------------------------
try:
    import mediapipe as mp
    _mp_pose  = mp.solutions.pose
    _mp_draw  = mp.solutions.drawing_utils
except AttributeError:
    from mediapipe import solutions as _sol
    _mp_pose  = _sol.pose
    _mp_draw  = _sol.drawing_utils

_POSE_STYLE = _mp_draw.DrawingSpec(color=(0, 255, 0),  thickness=2, circle_radius=3)
_CONN_STYLE = _mp_draw.DrawingSpec(color=(255, 255, 0), thickness=2)

# Landmarki 0-10 to twarz (nos, oczy, uszy, usta) — pomijamy je
_FACE_LANDMARKS = set(range(11))
_INVISIBLE      = _mp_draw.DrawingSpec(color=(0, 0, 0), thickness=0, circle_radius=0)

_BODY_CONNECTIONS = frozenset(
    (a, b) for a, b in _mp_pose.POSE_CONNECTIONS
    if a not in _FACE_LANDMARKS and b not in _FACE_LANDMARKS
)

# Słownik styli: twarz niewidoczna, reszta normalna
_LANDMARK_STYLE = {
    i: (_INVISIBLE if i in _FACE_LANDMARKS else _POSE_STYLE)
    for i in range(33)
}


def _qimage_to_bgr(img: QImage) -> np.ndarray:
    img = img.convertToFormat(QImage.Format.Format_RGB888)
    w, h = img.width(), img.height()
    arr  = np.frombuffer(img.bits(), dtype=np.uint8).reshape((h, w, 3)).copy()
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _bgr_to_qimage(bgr: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    return QImage(rgb.data, w, h, w * ch, QImage.Format.Format_RGB888).copy()


class PoseWorker(QObject):
    """
    Przetwarza klatki z kamery przez MediaPipe Pose w osobnym wątku.
    Kolejka ma rozmiar 1 — jeśli poprzednia klatka jeszcze się liczy,
    nowa ją zastępuje (brak narastającego opóźnienia).
    """

    frame_ready = Signal(QImage)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._queue: Queue[QImage | None] = Queue(maxsize=10)
        self._pose  = _mp_pose.Pose(
            model_complexity=0,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._thread  = Thread(target=self._run, daemon=True)
        self._running = False

    def start(self) -> None:
        self._running = True
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        try:
            self._queue.put_nowait(None)   # odblokuj wątek jeśli czeka
        except Exception:
            pass
        self._thread.join(timeout=2)
        self._pose.close()

    def submit(self, img: QImage) -> None:
        """Wrzuca klatkę do kolejki; jeśli jest pełna, stara klatka jest odrzucana."""
        try:
            self._queue.get_nowait()       # usuń starą (drop)
        except Exception:
            pass
        try:
            self._queue.put_nowait(img)
        except Exception:
            pass

    def _run(self) -> None:
        while self._running:
            try:
                img = self._queue.get(timeout=0.1)
            except Exception:
                continue

            if img is None:                # sygnał stopu
                break

            bgr     = _qimage_to_bgr(img)
            rgb     = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            results = self._pose.process(rgb)

            if results.pose_landmarks:
                _mp_draw.draw_landmarks(
                    bgr,
                    results.pose_landmarks,
                    _BODY_CONNECTIONS,
                    landmark_drawing_spec=_LANDMARK_STYLE,
                    connection_drawing_spec=_CONN_STYLE,
                )

            self.frame_ready.emit(_bgr_to_qimage(bgr))