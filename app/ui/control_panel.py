from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import QTimer, Qt, Signal


class ControlPanelWidget(QWidget):
    """
    Samodzielny widget panelu kontrolnego (Ciężar, Timer, Serie, Przyciski).
    Wysyła sygnały do głównego widoku, gdy użytkownik chce zakończyć serię lub trening.
    """

    end_set_requested = Signal()
    end_training_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("controlPanel")

        # Stan lokalny panelu
        self.current_weight: float = 60.0
        self.elapsed_seconds: int = 0
        self._timer_running: bool = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)

        self._setup_ui()

    def _setup_ui(self):
        cp_layout = QVBoxLayout(self)
        cp_layout.setContentsMargins(15, 15, 15, 15)
        cp_layout.setSpacing(15)

        weight_title = QLabel("CIĘŻAR:")
        weight_title.setObjectName("controlLabel")

        self._weight_label = QLabel(f"{self.current_weight:.1f} kg")
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

        weight_row = QWidget()
        w_layout = QHBoxLayout(weight_row)
        w_layout.setContentsMargins(0, 0, 0, 0)
        w_layout.setSpacing(8)
        w_layout.addWidget(weight_title)
        w_layout.addWidget(btn_minus)
        w_layout.addWidget(self._weight_label)
        w_layout.addWidget(btn_plus)
        w_layout.addStretch()

        cp_layout.addWidget(weight_row)

        self._timer_label = QLabel("CZAS: 00:00")
        self._timer_label.setObjectName("timerLabel")
        self._timer_label.setAlignment(Qt.AlignCenter)
        cp_layout.addWidget(self._timer_label)

        end_set_btn = QPushButton("✓  Zakończ serię")
        end_set_btn.setObjectName("endSetBtn")
        end_set_btn.clicked.connect(self.end_set_requested.emit)
        cp_layout.addWidget(end_set_btn)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("controlSeparator")
        cp_layout.addWidget(separator)

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

        sets_row = QWidget()
        sr_layout = QHBoxLayout(sets_row)
        sr_layout.setContentsMargins(0, 0, 0, 0)
        sr_layout.setSpacing(10)
        sr_layout.addWidget(sets_title, alignment=Qt.AlignTop)
        sr_layout.addWidget(self._sets_scroll, stretch=1)

        cp_layout.addWidget(sets_row, stretch=1)

        end_training_btn = QPushButton("Zakończ trening")
        end_training_btn.setObjectName("endTrainingBtn")
        end_training_btn.clicked.connect(self.end_training_requested.emit)
        cp_layout.addWidget(end_training_btn)

    # ── Logika Timera i Wagi ──────────────────────────────────────────────────

    def _change_weight(self, delta: float):
        self.current_weight = max(0.0, round(self.current_weight + delta, 1))
        self._weight_label.setText(f"{self.current_weight:.1f} kg")

    def _on_timer_tick(self):
        self.elapsed_seconds += 1
        self._timer_label.setText(f"CZAS: {self.format_time(self.elapsed_seconds)}")

    def start_timer(self):
        if not self._timer_running:
            self._timer.start()
            self._timer_running = True

    def pause_timer(self):
        if self._timer_running:
            self._timer.stop()
            self._timer_running = False

    @staticmethod
    def format_time(seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    # ── Zewnętrzne API dla TrainingView ───────────────────────────────────────

    def add_set_to_list(self, set_nr: int, reps: int, weight: float):
        lbl = QLabel(f"Seria {set_nr}:  {reps} powt.  –  {weight:.1f} kg")
        lbl.setObjectName("setLine")
        insert_pos = self._sets_list_layout.count() - 1
        self._sets_list_layout.insertWidget(insert_pos, lbl)

        QTimer.singleShot(50, lambda: self._sets_scroll.verticalScrollBar().setValue(
            self._sets_scroll.verticalScrollBar().maximum()
        ))

    def reset_panel(self):
        self.elapsed_seconds = 0
        self._timer_label.setText("CZAS: 00:00")
        self.pause_timer()

        while self._sets_list_layout.count() > 1:
            item = self._sets_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()