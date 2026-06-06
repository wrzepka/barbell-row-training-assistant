from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QWidget
)
from PySide6.QtCore import QTimer

from app.ui.base_view import BaseView
from app.ui.pose_camera import PoseCameraWidget
from app.ui.stats_widget import StatsWidget
from app.ui.skeleton_training_view import SkeletonTrainingView
from app.engine.analysis_worker import AnalysisWorker
from app.ui.control_panel import ControlPanelWidget
from app.db.database import add_training_entry
from app.utils.find_cameras import find_cameras


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
                                          ↓
                                   ControlWidget (umożliwia sterowanie treningiem)
                                          ↓
                                   TrainingView (spaja wszystko w całość)
    """

    def __init__(self):
        super().__init__(SkeletonTrainingView, "trainingView")

        self._analysis_worker = AnalysisWorker(parent=self)

        self._sets: list[dict] = []
        self._current_reps: int = 0

        self._create_widgets()
        self._setup_layout()
        self._connect_analysis()

    # ── Tworzenie widgetów ────────────────────────────────────────────────────

    def _create_widgets(self):
        camera_indexes = find_cameras()

        if len(camera_indexes) < 2:
            raise RuntimeError("Wymagane są 2 kamery.")

        side_idx = camera_indexes[0]
        front_idx = camera_indexes[1]

        print(f"[DEBUG] Inicjalizacja kamer: Bok={side_idx}, Przód={front_idx}")

        self.cam_side = PoseCameraWidget(side_idx)
        self.cam_front = PoseCameraWidget(front_idx,)

        self.stats_widget = StatsWidget()
        self.stats_widget.reset_btn.clicked.connect(self._on_reset_set)

        self.control_panel = ControlPanelWidget()
        self.control_panel.end_set_requested.connect(self._on_end_set)
        self.control_panel.end_training_requested.connect(self._on_end_training)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _setup_layout(self):
        main_layout = QHBoxLayout(self.content_page)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        cameras_layout = QVBoxLayout()
        cameras_layout.setSpacing(15)
        cameras_layout.addWidget(self.cam_side)
        cameras_layout.addWidget(self.cam_front)
        main_layout.addLayout(cameras_layout, stretch=3)

        side_panel = QWidget()
        side_panel.setMinimumWidth(350)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(15)

        side_layout.addWidget(self.stats_widget, stretch=0)
        side_layout.addWidget(self.control_panel, stretch=1)

        main_layout.addWidget(side_panel, stretch=2)

    # ── Podpięcie sygnałów i Sloty ────────────────────────────────────────────

    def _connect_analysis(self):
        self.cam_side.landmarks_ready.connect(self._analysis_worker.on_side_landmarks)
        self.cam_front.landmarks_ready.connect(self._analysis_worker.on_front_landmarks)
        self._analysis_worker.stats_updated.connect(self.stats_widget.update_stats)
        self._analysis_worker.stats_updated.connect(self._on_stats_updated)
        self._analysis_worker.rep_completed.connect(self._on_rep_completed)

    def _on_stats_updated(self, result):
        self._current_reps = result.reps

    def _on_rep_completed(self, reps: int):
        if reps == 1:
            self.control_panel.start_timer()

    def _on_end_set(self):
        if self._current_reps == 0:
            return

        set_nr = len(self._sets) + 1
        weight = self.control_panel.current_weight

        self._sets.append({
            "set_nr": set_nr,
            "reps": self._current_reps,
            "weight": weight,
        })

        # Przekazanie wizualizacji do panelu
        self.control_panel.add_set_to_list(set_nr, self._current_reps, weight)

        self.control_panel.pause_timer()
        self._analysis_worker.reset()
        self._current_reps = 0

    def _on_end_training(self):
        if self._current_reps > 0:
            self._on_end_set()

        if not self._sets:
            return

        total_reps = sum(s["reps"] for s in self._sets)
        total_sets = len(self._sets)
        total_volume = sum(s["reps"] * s["weight"] for s in self._sets)

        # Pobieramy czas z panelu
        seconds = self.control_panel.elapsed_seconds
        duration_str = ControlPanelWidget.format_time(seconds)

        sets_detail = [{"set_nr": s["set_nr"], "reps": s["reps"], "weight": s["weight"]} for s in self._sets]

        add_training_entry(
            weight=total_volume, reps=total_reps, sets=total_sets,
            duration=duration_str, score=80, to_fix_list=[], sets_detail=sets_detail
        )

        self._sets.clear()
        self._current_reps = 0
        self.control_panel.reset_panel()
        self._analysis_worker.reset()

    def _on_reset_set(self):
        self._analysis_worker.reset()
        self._current_reps = 0

    # ── Cykl życia kamer ──────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self.cam_side.start_camera()
        QTimer.singleShot(500, self.cam_front.start_camera)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.cam_side.stop_camera()
        self.cam_front.stop_camera()

    def closeEvent(self, event):
        self.cam_side.stop_camera()
        self.cam_front.stop_camera()
        super().closeEvent(event)