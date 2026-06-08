# Zawartość pliku: app/ui/debug_panel.py
"""
DebugPanel – tymczasowy widget symulacji powtórzeń bez kamery.

Używany wyłącznie gdy DEBUG_MODE = True w app/core/config.py.
Emituje sygnały identyczne z tymi, które normalnie generuje AnalysisWorker,
dzięki czemu reszta aplikacji (StatsWidget, ControlPanel, zapis do bazy)
działa bez żadnych zmian.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class DebugPanel(QWidget):
    """
    Panel do ręcznego nabijania / odejmowania powtórzeń podczas testów bez kamery.

    Użycie:
        panel = DebugPanel(analysis_worker, control_panel)
        layout.addWidget(panel)
    """

    def __init__(self, analysis_worker, control_panel, parent=None):
        super().__init__(parent)
        self._worker = analysis_worker
        self._control = control_panel
        self._reps = 0

        self.setObjectName("debugPanel")
        self.setStyleSheet(
            "QWidget#debugPanel {"
            "  background: #3a2a00;"
            "  border: 1px solid #cc8800;"
            "  border-radius: 6px;"
            "}"
            "QLabel {"
            "  color: #ffcc44;"
            "  font-size: 11px;"
            "}"
            "QPushButton {"
            "  background: #cc8800;"
            "  color: black;"
            "  font-weight: bold;"
            "  border-radius: 4px;"
            "  padding: 4px 12px;"
            "}"
            "QPushButton:pressed { background: #ffaa00; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        title = QLabel("⚠ TRYB DEBUG – symulacja kamery")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_minus = QPushButton("− Usuń powt.")
        btn_minus.clicked.connect(self._remove_rep)

        btn_plus = QPushButton("+ Dodaj powt.")
        btn_plus.clicked.connect(self._add_rep)

        btn_row.addWidget(btn_minus)
        btn_row.addWidget(btn_plus)
        layout.addLayout(btn_row)

    def reset(self) -> None:
        """Resetuje wewnętrzny licznik (wywoływane przy reset serii)."""
        self._reps = 0
        

    def _add_rep(self) -> None:
        """Symuluje zaliczenie jednego powtórzenia."""
        self._reps += 1
        if self._reps == 1:
            self._control.start_timer()
        self._emit(new_rep=True)

    def _remove_rep(self) -> None:
        """Usuwa jedno powtórzenie (korekta pomyłki)."""
        if self._reps > 0:
            self._reps -= 1
        self._emit(new_rep=False)

    def _emit(self, new_rep: bool) -> None:
        from app.engine.analysis_worker import AnalysisResult
        self._worker.stats_updated.emit(
            AnalysisResult(reps=self._reps, phase="PULLING", errors=[], new_rep=new_rep)
        )