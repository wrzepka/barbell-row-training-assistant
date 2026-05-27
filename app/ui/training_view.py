from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from PySide6.QtCore import QTimer

from app.ui.base_view import BaseView
from app.ui.pose_camera import PoseCameraWidget
from app.ui.stats_widget import StatsWidget
from app.ui.skeleton_training_view import SkeletonTrainingView
from app.engine.analysis_worker import AnalysisWorker


class TrainingView(BaseView):
    """
    Widok treningowy z podglądem z dwóch kamer, szkieletem MediaPipe
    i analizą techniki wiosłowania sztangą.

    Architektura przepływu danych:
        CameraWorker → PoseWorker → PoseCameraWidget.landmarks_ready
                                          ↓
                                   AnalysisWorker (liczy powt. + błędy)
                                          ↓
                                   StatsWidget (wyświetla wyniki)
    """

    def __init__(self):
        super().__init__(SkeletonTrainingView, "trainingView")

        self._analysis_worker = AnalysisWorker(parent=self)

        self._create_widgets()
        self._setup_layout()
        self._connect_analysis()

    def _create_widgets(self):
        # TODO: ogarnąć sposób na dobre szukanie indeksów kamer
        side_idx = 1
        front_idx = 2

        print(f"[DEBUG] Inicjalizacja kamer: Bok={side_idx}, Przód={front_idx}")

        # Kamera boczna
        self.cam_side = PoseCameraWidget(side_idx, "KAMERA 1\n(Bok)")

        # Kamera przednia
        self.cam_front = PoseCameraWidget(front_idx, "KAMERA 2\n(Przód)")

        # Inicjalizacja widżetu statystyk
        self.stats_widget = StatsWidget()
        self.stats_widget.reset_btn.clicked.connect(self._on_reset)

    def _setup_layout(self):
        main_layout = QVBoxLayout(self.content_page)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        cameras_layout = QHBoxLayout()
        cameras_layout.setSpacing(15)
        cameras_layout.addWidget(self.cam_side)
        cameras_layout.addWidget(self.cam_front)

        main_layout.addLayout(cameras_layout, stretch=6)
        main_layout.addWidget(self.stats_widget, stretch=2)

    def _connect_analysis(self):
        """
        Podpina sygnały landmarków z obu kamer do AnalysisWorker.
        Boczna → on_side_landmarks (liczy powt. + bujanie/plecy)
        Przednia → on_front_landmarks (flaring łokci)
        """
        self.cam_side.landmarks_ready.connect(self._analysis_worker.on_side_landmarks)
        self.cam_front.landmarks_ready.connect(self._analysis_worker.on_front_landmarks)
        self._analysis_worker.stats_updated.connect(self.stats_widget.update_stats)

    def _on_reset(self):
        """Resetuje licznik i analizę — np. między setami."""
        self._analysis_worker.reset()

    # ── Cykl życia ────────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)

        print("[DEBUG] showEvent: Uruchamianie kamery 1 (Bok)...")
        self.cam_side.start_camera()
        QTimer.singleShot(750, self._start_second_camera)

    def _start_second_camera(self):
        print("[DEBUG] showEvent: Uruchamianie kamery 2 (Przód)...")
        self.cam_front.start_camera()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.cam_side.stop_camera()
        self.cam_front.stop_camera()

    def closeEvent(self, event):
        self.cam_side.stop_camera()
        self.cam_front.stop_camera()
        super().closeEvent(event)