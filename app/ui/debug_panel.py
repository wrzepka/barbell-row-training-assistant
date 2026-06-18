# Zawartość pliku: app/ui/debug_panel.py
"""
DebugPanel – tymczasowy widget symulacji powtórzeń i błędów techniki bez kamery.

Używany wyłącznie gdy DEBUG_MODE = True w app/core/config.py.
Emituje sygnały identyczne z tymi, które normalnie generuje AnalysisWorker,
dzięki czemu reszta aplikacji (StatsWidget, ControlPanel, zapis do bazy)
działa bez żadnych zmian.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout,
    QFrame,
)
from PySide6.QtCore import Qt

# Wszystkie kody błędów i ich opisy – wzięte z form_analyzer.py
# format: (code, label_wyświetlany, message_do_AnalysisResult, severity)
_ALL_ERRORS = [
    (
        "ROUNDED_BACK",
        "Zaokrąglone plecy",
        "Zaokrąglone plecy! Trzymaj prosty tułów.",
        0.8,
    ),
    (
        "SWINGING",
        "Bujanie tułowiem",
        "Bujanie tułowiem! Stabilizuj pozycję.",
        0.7,
    ),
    (
        "ELBOW_FLARE",
        "Łokcie za szeroko",
        "Łokcie za szeroko! Prowadź je blisko ciała.",
        0.6,
    ),
    (
        "KNEE_FORWARD",
        "Zginanie kolan",
        "Zginasz kolana! Wypchnij biodra w tył.",
        0.5,
    ),
    (
        "TORSO_ANGLE",
        "Zły kąt tułowia",
        "Pochyl tułów ~45° (zbyt pionowo lub zbyt nisko).",
        0.5,
    ),
]


class DebugPanel(QWidget):
    """
    Panel do ręcznego nabijania / odejmowania powtórzeń i symulowania błędów
    techniki podczas testów bez kamery.

    Każdy błąd ma osobny przycisk toggle – wciśnięty = błąd jest aktywny
    i zostanie wysłany w każdym kolejnym emit().  Dzięki temu TrainingView
    widzi „nowy błąd" dokładnie raz (przy pierwszym wciśnięciu), tak samo
    jak przy błędach rozpoznawanych przez SmoothFlag w prawdziwej analizie.

    Użycie:
        panel = DebugPanel(analysis_worker, control_panel)
        layout.addWidget(panel)
    """

    # ── Styl ──────────────────────────────────────────────────────────────────

    _STYLE = (
        "QWidget#debugPanel {"
        "  background: #2a1a00;"
        "  border: 1px solid #cc8800;"
        "  border-radius: 6px;"
        "}"
        "QLabel#title {"
        "  color: #ffcc44;"
        "  font-size: 11px;"
        "  font-weight: bold;"
        "}"
        "QLabel#sectionLabel {"
        "  color: #cc9922;"
        "  font-size: 10px;"
        "}"
        "QFrame#separator {"
        "  color: #554400;"
        "}"
        # Przyciski powtórzeń
        "QPushButton#repBtn {"
        "  background: #cc8800;"
        "  color: black;"
        "  font-weight: bold;"
        "  border-radius: 4px;"
        "  padding: 4px 12px;"
        "}"
        "QPushButton#repBtn:pressed { background: #ffaa00; }"
        # Przyciski błędów – nieaktywne
        "QPushButton#errBtn {"
        "  background: #3d2200;"
        "  color: #cc8800;"
        "  font-size: 10px;"
        "  border: 1px solid #554400;"
        "  border-radius: 4px;"
        "  padding: 3px 6px;"
        "  text-align: left;"
        "}"
        # Przyciski błędów – aktywne (błąd włączony)
        "QPushButton#errBtn[active=true] {"
        "  background: #7a1a00;"
        "  color: #ff6644;"
        "  border: 1px solid #cc3300;"
        "}"
        "QPushButton#errBtn:pressed { background: #552200; }"
    )

    # ── Inicjalizacja ─────────────────────────────────────────────────────────

    def __init__(self, analysis_worker, control_panel, parent=None):
        super().__init__(parent)
        self._worker = analysis_worker
        self._control = control_panel
        self._reps = 0

        # Zbiór aktualnie aktywnych kodów błędów
        self._active_errors: set[str] = set()

        # Mapowanie kod → QPushButton (do aktualizacji stylu)
        self._error_buttons: dict[str, QPushButton] = {}

        self.setObjectName("debugPanel")
        self.setStyleSheet(self._STYLE)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Tytuł
        title = QLabel("⚠ TRYB DEBUG – symulacja kamery")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Separator
        layout.addWidget(self._make_separator())

        # Sekcja powtórzeń
        rep_label = QLabel("POWTÓRZENIA")
        rep_label.setObjectName("sectionLabel")
        layout.addWidget(rep_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_minus = QPushButton("− Usuń powt.")
        btn_minus.setObjectName("repBtn")
        btn_minus.clicked.connect(self._remove_rep)

        btn_plus = QPushButton("+ Dodaj powt.")
        btn_plus.setObjectName("repBtn")
        btn_plus.clicked.connect(self._add_rep)

        btn_row.addWidget(btn_minus)
        btn_row.addWidget(btn_plus)
        layout.addLayout(btn_row)

        # Separator
        layout.addWidget(self._make_separator())

        # Sekcja błędów techniki
        err_label = QLabel("BŁĘDY TECHNIKI  (kliknij = włącz / wyłącz)")
        err_label.setObjectName("sectionLabel")
        layout.addWidget(err_label)

        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)

        for i, (code, label, _msg, _sev) in enumerate(_ALL_ERRORS):
            btn = QPushButton(label)
            btn.setObjectName("errBtn")
            btn.setProperty("active", False)
            btn.setCheckable(False)           # stan trzymamy sami
            btn.clicked.connect(lambda _checked, c=code: self._toggle_error(c))
            grid.addWidget(btn, i // 2, i % 2)
            self._error_buttons[code] = btn

        layout.addLayout(grid)

        # Przycisk „wyczyść wszystkie błędy"
        clear_btn = QPushButton("✕  Wyczyść wszystkie błędy")
        clear_btn.setObjectName("repBtn")
        clear_btn.clicked.connect(self._clear_errors)
        layout.addWidget(clear_btn)

    @staticmethod
    def _make_separator() -> QFrame:
        line = QFrame()
        line.setObjectName("separator")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    # ── Logika powtórzeń ──────────────────────────────────────────────────────

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

    # ── Logika błędów ─────────────────────────────────────────────────────────

    def _toggle_error(self, code: str) -> None:
        """Włącza lub wyłącza dany błąd i natychmiast wysyła aktualny stan."""
        if code in self._active_errors:
            self._active_errors.discard(code)
        else:
            self._active_errors.add(code)
        self._refresh_error_button(code)
        self._emit(new_rep=False)

    def _clear_errors(self) -> None:
        """Wyłącza wszystkie aktywne błędy naraz."""
        for code in list(self._active_errors):
            self._active_errors.discard(code)
            self._refresh_error_button(code)
        self._emit(new_rep=False)

    def _refresh_error_button(self, code: str) -> None:
        """Aktualizuje wygląd przycisku (active=true/false) i wymusza reaplikację CSS."""
        btn = self._error_buttons.get(code)
        if btn is None:
            return
        is_active = code in self._active_errors
        btn.setProperty("active", is_active)
        # Qt wymaga polish/unpolish żeby dynamiczna zmiana property odświeżyła styl
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Resetuje licznik i błędy (wywoływane przy reset serii)."""
        self._reps = 0
        self._clear_errors()

    # ── Emisja sygnału ────────────────────────────────────────────────────────

    def _emit(self, new_rep: bool) -> None:
        from app.engine.analysis_worker import AnalysisResult
        from app.engine.form_analyzer import FormError

        errors = [
            FormError(code=code, message=msg, severity=sev)
            for code, _label, msg, sev in _ALL_ERRORS
            if code in self._active_errors
        ]

        self._worker.stats_updated.emit(
            AnalysisResult(reps=self._reps, phase="PULLING", errors=errors, new_rep=new_rep)
        )