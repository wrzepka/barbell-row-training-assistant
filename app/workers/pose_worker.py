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

_FACE_LANDMARKS = set(range(11))
_INVISIBLE      = _mp_draw.DrawingSpec(color=(0, 0, 0), thickness=0, circle_radius=0)

_BODY_CONNECTIONS = frozenset(
    (a, b) for a, b in _mp_pose.POSE_CONNECTIONS
    if a not in _FACE_LANDMARKS and b not in _FACE_LANDMARKS
)

_LANDMARK_STYLE = {
    i: (_INVISIBLE if i in _FACE_LANDMARKS else _POSE_STYLE)
    for i in range(33)
}

# ---------------------------------------------------------------------------
# Analizator wiosłowania
# ---------------------------------------------------------------------------
from app.engine.rowing_analyzer import RowingAnalyzer, RowingAnalysis

# Kolory nakładki na obraz (BGR) dla każdego poziomu ważności
_SEVERITY_COLOR = {
    "ok":      (0,   200,  0),    # zielony
    "warning": (0,   165, 255),   # pomarańczowy
    "error":   (0,   0,   220),   # czerwony
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


def _draw_analysis_overlay(bgr: np.ndarray, analysis: RowingAnalysis) -> None:
    """
    Rysuje na klatce listę komunikatów z wyników analizy.
    Każdy wiersz jest kolorowany według severity: zielony / pomarańczowy / czerwony.
    Wywoływane tylko gdy analysis.visible == True.
    """
    if not analysis.visible:
        return

    x, y_start, line_h = 10, 30, 26
    font     = cv2.FONT_HERSHEY_SIMPLEX
    scale    = 0.62
    bg_color = (30, 30, 30)

    for i, check in enumerate(analysis.checks):
        color = _SEVERITY_COLOR.get(check.severity, (200, 200, 200))
        text  = check.message
        y     = y_start + i * line_h

        # ciemne tło pod tekstem dla czytelności
        (tw, th), _ = cv2.getTextSize(text, font, scale, 1)
        cv2.rectangle(bgr, (x - 2, y - th - 2), (x + tw + 2, y + 2), bg_color, -1)
        cv2.putText(bgr, text, (x, y), font, scale, color, 1, cv2.LINE_AA)


class PoseWorker(QObject):
    """
    Przetwarza klatki z kamery przez MediaPipe Pose w osobnym wątku.

    Sygnały
    -------
    frame_ready     : QImage  – klatka z narysowanym szkieletem (i opcjonalną
                                nakładką analizy wiosłowania)
    analysis_ready  : object  – obiekt RowingAnalysis z wynikami sprawdzeń
                                (emitowany tylko gdy rowing_check_enabled=True)
    """

    frame_ready    = Signal(QImage)
    analysis_ready = Signal(object)   # RowingAnalysis

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

        # --- analizator wiosłowania ---
        self._rowing_analyzer      = RowingAnalyzer()
        self._rowing_check_enabled = False   # włącz przez enable_rowing_check()

    # -----------------------------------------------------------------------
    # Sterowanie analizą wiosłowania
    # -----------------------------------------------------------------------

    def enable_rowing_check(self) -> None:
        """Włącza sprawdzanie kątów wiosłowania i rysowanie nakładki."""
        self._rowing_check_enabled = True

    def disable_rowing_check(self) -> None:
        """Wyłącza sprawdzanie kątów wiosłowania."""
        self._rowing_check_enabled = False

    # -----------------------------------------------------------------------
    # Cykl życia wątku
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # Główna pętla wątku
    # -----------------------------------------------------------------------

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
                # Rysuj szkielet
                _mp_draw.draw_landmarks(
                    bgr,
                    results.pose_landmarks,
                    _BODY_CONNECTIONS,
                    landmark_drawing_spec=_LANDMARK_STYLE,
                    connection_drawing_spec=_CONN_STYLE,
                )

                # Analiza wiosłowania (tylko gdy włączona)
                if self._rowing_check_enabled:
                    analysis = self._rowing_analyzer.analyze(
                        results.pose_landmarks.landmark
                    )
                    _draw_analysis_overlay(bgr, analysis)
                    self.analysis_ready.emit(analysis)

            self.frame_ready.emit(_bgr_to_qimage(bgr))