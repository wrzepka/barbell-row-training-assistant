from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame,
)
from PySide6.QtCore import QTimer, Qt

from app.ui.base_view import BaseView
from app.ui.pose_camera import PoseCameraWidget
from app.ui.stats_widget import StatsWidget
from app.ui.skeleton_training_view import SkeletonTrainingView
from app.engine.analysis_worker import AnalysisWorker
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
                          TrainingView (zarządza seriami, timerem, bazą)
    """

    def __init__(self):
        super().__init__(SkeletonTrainingView, "trainingView")

        self._analysis_worker = AnalysisWorker(parent=self)

        # ── Stan tymczasowy treningu ───────────────────────────────────────────
        self._sets: list[dict] = []      # {set_nr, reps, weight}
        self._current_reps: int = 0
        self._weight: float = 60.0

        # ── Timer ──────────────────────────────────────────────────────────────
        self._elapsed_seconds: int = 0
        self._timer_running: bool = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)

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

        self.cam_side = PoseCameraWidget(side_idx, "KAMERA 1\n(Bok)")
        self.cam_front = PoseCameraWidget(front_idx, "KAMERA 2\n(Przód)")

        self.stats_widget = StatsWidget()
        self.stats_widget.reset_btn.clicked.connect(self._on_reset_set)

        # --- Wybór ciężaru ---
        weight_title = QLabel("CIĘŻAR:")
        weight_title.setObjectName("controlLabel")

        self._weight_label = QLabel(f"{self._weight:.1f} kg")
        self._weight_label.setObjectName("weightValue")
        self._weight_label.setAlignment(Qt.AlignCenter)
        self._weight_label.setMinimumWidth(80)

        btn_minus = QPushButton("−")
        btn_minus.setObjectName("weightBtn")
        btn_minus.setFixedSize(36, 36)
        btn_minus.clicked.connect(lambda: self._change_weight(-2.5))

        btn_plus = QPushButton("+")
        btn_plus.setObjectName("weightBtn")
        btn_plus.setFixedSize(36, 36)
        btn_plus.clicked.connect(lambda: self._change_weight(2.5))

        self._weight_row = QWidget()
        w_layout = QHBoxLayout(self._weight_row)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.setSpacing(8)
        w_layout.addWidget(weight_title)
        w_layout.addWidget(btn_minus)
        w_layout.addWidget(self._weight_label)
        w_layout.addWidget(btn_plus)
        w_layout.addStretch()

        # --- Timer ---
        self._timer_label = QLabel("CZAS: 00:00")
        self._timer_label.setObjectName("timerLabel")
        self._timer_label.setAlignment(Qt.AlignCenter)

        # --- Przycisk "Zakończ serię" ---
        self._end_set_btn = QPushButton("✓  Zakończ serię")
        self._end_set_btn.setObjectName("endSetBtn")
        self._end_set_btn.clicked.connect(self._on_end_set)

        # --- Lista wykonanych serii ---
        sets_title = QLabel("WYKONANE SERIE:")
        sets_title.setObjectName("setsTitle")
        sets_title.setAlignment(Qt.AlignTop)

        self._sets_list_layout = QVBoxLayout()
        self._sets_list_layout.setContentsMargins(0, 0, 0, 0)
        self._sets_list_layout.setSpacing(3)
        self._sets_list_layout.addStretch()

        sets_container = QWidget()
        sets_container.setObjectName("setsContainer")
        sets_container.setLayout(self._sets_list_layout)

        self._sets_scroll = QScrollArea()
        self._sets_scroll.setWidget(sets_container)
        self._sets_scroll.setWidgetResizable(True)
        self._sets_scroll.setFixedHeight(72)
        self._sets_scroll.setFrameShape(QFrame.NoFrame)

        self._sets_row = QWidget()
        sr_layout = QHBoxLayout(self._sets_row)
        sr_layout.setContentsMargins(0, 0, 0, 0)
        sr_layout.setSpacing(10)
        sr_layout.addWidget(sets_title, alignment=Qt.AlignTop)
        sr_layout.addWidget(self._sets_scroll, stretch=1)

        # --- Przycisk "Zakończ trening" ---
        self._end_training_btn = QPushButton("⬛  Zakończ trening")
        self._end_training_btn.setObjectName("endTrainingBtn")
        self._end_training_btn.clicked.connect(self._on_end_training)

    # ── Layout ────────────────────────────────────────────────────────────────

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

        # --- Panel kontrolny ---
        control_panel = QWidget()
        control_panel.setObjectName("controlPanel")
        cp_layout = QVBoxLayout(control_panel)
        cp_layout.setContentsMargins(12, 10, 12, 10)
        cp_layout.setSpacing(10)

        # Górny wiersz: ciężar | timer | zakończ serię
        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.addWidget(self._weight_row, stretch=2)
        top_row.addWidget(self._timer_label, stretch=1)
        top_row.addWidget(self._end_set_btn, stretch=1)
        cp_layout.addLayout(top_row)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("controlSeparator")
        cp_layout.addWidget(separator)

        # Lista serii
        cp_layout.addWidget(self._sets_row)

        # Przycisk zakończenia treningu
        cp_layout.addWidget(self._end_training_btn)

        main_layout.addWidget(control_panel, stretch=0)

    # ── Podpięcie sygnałów ────────────────────────────────────────────────────

    def _connect_analysis(self):
        """
        Boczna → on_side_landmarks (liczy powt. + bujanie/plecy)
        Przednia → on_front_landmarks (flaring łokci)
        """
        self.cam_side.landmarks_ready.connect(self._analysis_worker.on_side_landmarks)
        self.cam_front.landmarks_ready.connect(self._analysis_worker.on_front_landmarks)

        # Aktualizacja StatsWidget i lokalnego licznika powtórzeń
        self._analysis_worker.stats_updated.connect(self.stats_widget.update_stats)
        self._analysis_worker.stats_updated.connect(self._on_stats_updated)

        # Automatyczny start timera przy pierwszym powtórzeniu serii
        self._analysis_worker.rep_completed.connect(self._on_rep_completed)

    # ── Sloty ─────────────────────────────────────────────────────────────────

    def _on_stats_updated(self, result) -> None:
        """Aktualizuje lokalny licznik powtórzeń na podstawie sygnału z AnalysisWorker."""
        self._current_reps = result.reps

    def _on_rep_completed(self, reps: int) -> None:
        """Automatycznie uruchamia timer przy pierwszym powtórzeniu nowej serii."""
        if reps == 1 and not self._timer_running:
            self._start_timer()

    def _on_end_set(self) -> None:
        """Zapisuje bieżącą serię do pamięci tymczasowej, pauzuje timer i resetuje licznik."""
        if self._current_reps == 0:
            return

        set_nr = len(self._sets) + 1
        self._sets.append({
            "set_nr": set_nr,
            "reps": self._current_reps,
            "weight": self._weight,
        })
        self._append_set_label(set_nr, self._current_reps, self._weight)

        self._pause_timer()
        self._analysis_worker.reset()
        self._current_reps = 0

    def _on_end_training(self) -> None:
        """
        Zapisuje cały trening do bazy danych (sumuje dane ze wszystkich serii)
        i resetuje widok do stanu początkowego.
        """
        # Jeśli jest niedokończona seria, dorzucamy ją automatycznie
        if self._current_reps > 0:
            self._on_end_set()

        if not self._sets:
            return

        total_reps = sum(s["reps"] for s in self._sets)
        total_sets = len(self._sets)
        # Łączny wolumen = suma (powtórzenia × ciężar) dla każdej serii
        total_volume = sum(s["reps"] * s["weight"] for s in self._sets)
        duration_str = self._format_time(self._elapsed_seconds)
        score = 80  # TODO: zastąpić rzeczywistą logiką oceny techniki

        # Szczegóły każdej serii zapisywane osobno
        sets_detail = [
            {"set_nr": s["set_nr"], "reps": s["reps"], "weight": s["weight"]}
            for s in self._sets
        ]

        add_training_entry(
            weight=total_volume,
            reps=total_reps,
            sets=total_sets,
            duration=duration_str,
            score=score,
            to_fix_list=[],
            sets_detail=sets_detail,
        )
        print(f"[INFO] Zapisano trening: {total_sets} serie, {total_reps} powt., "
              f"{total_volume:.1f} kg objętości, czas {duration_str}")

        self._reset_training()

    def _on_reset_set(self) -> None:
        """Resetuje bieżący licznik serii (przycisk Reset w StatsWidget)."""
        self._analysis_worker.reset()
        self._current_reps = 0

    def _on_timer_tick(self) -> None:
        self._elapsed_seconds += 1
        self._timer_label.setText(f"CZAS: {self._format_time(self._elapsed_seconds)}")

    # ── Ciężar ────────────────────────────────────────────────────────────────

    def _change_weight(self, delta: float) -> None:
        self._weight = max(0.0, round(self._weight + delta, 1))
        self._weight_label.setText(f"{self._weight:.1f} kg")

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _start_timer(self) -> None:
        if not self._timer_running:
            self._timer.start()
            self._timer_running = True

    def _pause_timer(self) -> None:
        if self._timer_running:
            self._timer.stop()
            self._timer_running = False

    @staticmethod
    def _format_time(seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    # ── Lista serii ───────────────────────────────────────────────────────────

    def _append_set_label(self, set_nr: int, reps: int, weight: float) -> None:
        """Dodaje wiersz do listy wykonanych serii (przed końcowym stretch)."""
        lbl = QLabel(f"Seria {set_nr}:  {reps} powt.  –  {weight:.1f} kg")
        lbl.setObjectName("setLine")
        # Wstawiamy przed stretch (zawsze ostatni element layoutu)
        insert_pos = self._sets_list_layout.count() - 1
        self._sets_list_layout.insertWidget(insert_pos, lbl)
        # Przewijamy na dół po dodaniu nowego wpisu
        QTimer.singleShot(50, lambda: self._sets_scroll.verticalScrollBar().setValue(
            self._sets_scroll.verticalScrollBar().maximum()
        ))

    # ── Reset całego treningu ─────────────────────────────────────────────────

    def _reset_training(self) -> None:
        self._sets.clear()
        self._current_reps = 0
        self._elapsed_seconds = 0
        self._timer_label.setText("CZAS: 00:00")
        self._pause_timer()
        self._analysis_worker.reset()

        # Usuwa wszystkie etykiety serii (zostawia końcowy stretch)
        while self._sets_list_layout.count() > 1:
            item = self._sets_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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