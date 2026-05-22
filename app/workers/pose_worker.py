from __future__ import annotations

from queue import Queue
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

# Połączenia ciała (bez twarzy)
_BODY_CONNECTIONS = frozenset(
    (a, b) for a, b in _mp_pose.POSE_CONNECTIONS
    if a not in _FACE_LANDMARKS and b not in _FACE_LANDMARKS
)


def _qimage_to_bgr(img: QImage) -> np.ndarray:
    img = img.convertToFormat(QImage.Format.Format_RGB888)
    w, h = img.width(), img.height()
    arr  = np.frombuffer(img.bits(), dtype=np.uint8).reshape((h, w, 3)).copy()
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _bgr_to_qimage(bgr: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    return QImage(rgb.data, w, h, w * ch, QImage.Format.Format_RGB888).copy()


def _draw_pose(image: np.ndarray, landmarks, connections, landmark_style, connection_style):
    """
    Rysuje tylko podane połączenia i tylko landmarki z indeksów >= 11.
    """
    h, w, _ = image.shape
    for a, b in connections:
        pt_a = (int(landmarks[a].x * w), int(landmarks[a].y * h))
        pt_b = (int(landmarks[b].x * w), int(landmarks[b].y * h))
        cv2.line(image, pt_a, pt_b, connection_style.color, connection_style.thickness)

    for idx in range(11, 33):
        cx = int(landmarks[idx].x * w)
        cy = int(landmarks[idx].y * h)
        cv2.circle(image, (cx, cy),
                   radius=landmark_style.circle_radius,
                   color=landmark_style.color,
                   thickness=landmark_style.thickness)


class PoseWorker(QObject):
    """
    Przetwarza klatki z kamery przez MediaPipe Pose w osobnym wątku.

    Sygnały
    -------
    frame_ready(QImage)
        Klatka z narysowanym szkieletem — do wyświetlenia w UI.
    landmarks_ready(list)
        Surowe landmarki MediaPipe — do analizy techniki (AnalysisWorker).
        Emitowane tylko gdy MediaPipe wykryje sylwetkę.
    """

    frame_ready     = Signal(QImage)
    landmarks_ready = Signal(object)   # lista landmarks MediaPipe

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
            self._queue.put_nowait(None)
        except Exception:
            pass
        self._thread.join(timeout=2)
        self._pose.close()

    def submit(self, img: QImage) -> None:
        """Wrzuca klatkę do kolejki; jeśli jest pełna, stara klatka jest odrzucana."""
        try:
            self._queue.get_nowait()
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

            if img is None:
                break

            bgr     = _qimage_to_bgr(img)
            rgb     = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            results = self._pose.process(rgb)

            if results.pose_landmarks:
                _draw_pose(
                    bgr,
                    results.pose_landmarks.landmark,
                    _BODY_CONNECTIONS,
                    _POSE_STYLE,
                    _CONN_STYLE,
                )
                # Emituj landmarki do analizy techniki
                self.landmarks_ready.emit(results.pose_landmarks.landmark)

            self.frame_ready.emit(_bgr_to_qimage(bgr))