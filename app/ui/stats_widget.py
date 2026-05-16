from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

from app.analysis.analysis_worker import AnalysisResult


class StatsWidget(QWidget):
    """
    Panel statystyk wyświetlany pod kamerami w widoku treningowym.
    Pokazuje licznik powtórzeń i aktywne błędy techniki.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statsWidget")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(30)

        # ── Licznik powtórzeń ─────────────────────────────────────────────
        reps_layout = QVBoxLayout()

        reps_title = QLabel("POWTÓRZENIA")
        reps_title.setObjectName("statsLabel")
        reps_title.setAlignment(Qt.AlignCenter)

        self.reps_counter = QLabel("0")
        self.reps_counter.setObjectName("repsCounter")
        self.reps_counter.setAlignment(Qt.AlignCenter)

        self.phase_label = QLabel("—")
        self.phase_label.setObjectName("phaseLabel")
        self.phase_label.setAlignment(Qt.AlignCenter)

        self.reset_btn = QPushButton("Resetuj")
        self.reset_btn.setObjectName("resetButton")
        self.reset_btn.setCursor(Qt.PointingHandCursor)

        reps_layout.addWidget(reps_title)
        reps_layout.addWidget(self.reps_counter)
        reps_layout.addWidget(self.phase_label)
        reps_layout.addWidget(self.reset_btn)

        # ── Błędy techniki ────────────────────────────────────────────────
        errors_layout = QVBoxLayout()

        errors_title = QLabel("TECHNIKA")
        errors_title.setObjectName("statsLabel")
        errors_title.setAlignment(Qt.AlignCenter)

        self.error_labels: dict[str, QLabel] = {
            "ROUNDED_BACK": self._make_error_label("Zaokrąglone plecy"),
            "SWINGING":     self._make_error_label("Bujanie tułowiem"),
            "ELBOW_FLARE":  self._make_error_label("Łokcie za szeroko"),
        }

        errors_layout.addWidget(errors_title)
        for lbl in self.error_labels.values():
            errors_layout.addWidget(lbl)
        errors_layout.addStretch()

        main_layout.addLayout(reps_layout,   stretch=1)
        main_layout.addLayout(errors_layout, stretch=2)

    def _make_error_label(self, text: str) -> QLabel:
        lbl = QLabel(f"● {text}")
        lbl.setObjectName("errorLabel")
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl.setVisible(False)   # ukryte dopóki błąd nieaktywny
        return lbl

    # ── publiczne API ─────────────────────────────────────────────────────

    def update_stats(self, result: AnalysisResult):
        """Slot podpięty do AnalysisWorker.stats_updated."""
        self.reps_counter.setText(str(result.reps))

        phase_map = {
            "PULLING":  "↑ Podciąganie",
            "LOWERING": "↓ Opuszczanie",
            "IDLE":     "— Czekam…",
        }
        self.phase_label.setText(phase_map.get(result.phase, "—"))

        # Pokaż/ukryj błędy
        active_codes = {e.code for e in result.errors}
        for code, lbl in self.error_labels.items():
            lbl.setVisible(code in active_codes)