from __future__ import annotations
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from app.engine.rep_counter import RepCounter
from app.engine.form_analyzer import SideFormAnalyzer, FrontFormAnalyzer, FormError


@dataclass
class AnalysisResult:
    reps:           int
    phase:          str              # "CALIBRATING" | "IDLE" | "PULLING" | "TOP" | "LOWERING"
    errors:         list[FormError]  # aktywne błędy techniki (z obu kamer)
    new_rep:        bool             # True tylko w klatce gdy zaliczono nowe powt.
    calib_progress: float = 0.0     # 0.0–1.0 podczas kalibracji, 1.0 po


class AnalysisWorker(QObject):

    stats_updated = Signal(object)   # AnalysisResult
    rep_completed = Signal(int)      # liczba powtórzeń

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._counter      = RepCounter()
        self._side_analyzer  = SideFormAnalyzer()
        self._front_analyzer = FrontFormAnalyzer()

        self._side_errors:  list[FormError] = []
        self._front_errors: list[FormError] = []

    # ── sloty ─────────────────────────────────────────────────────────────────

    # Kody błędów które blokują zaliczenie powtórzenia.
    # Blokada działa tylko gdy SmoothFlag już się "napełniła" (błąd w errors),
    # NIE na surowym kącie klatka-po-klatce – dzięki temu pierwsze klatki
    # nie kickują licznika z IDLE zanim sylwetka się ustabilizuje.
    _BLOCKING_ERRORS = frozenset({"ROUNDED_BACK", "TORSO_ANGLE", "KNEE_FORWARD"})

    def on_side_landmarks(self, landmarks) -> None:
        """
        Slot podpięty do PoseWorker kamery BOCZNEJ.
        Liczy powtórzenia i wykrywa błędy widoczne z boku.
        """
        self._side_errors = self._side_analyzer.analyze(landmarks)

        # TORSO_ANGLE blokuje zliczanie – wykrywa stanie prosto i brak pozycji.
        # ROUNDED_BACK i KNEE_FORWARD tylko ostrzegają, nie blokują.
        blocking = any(e.code == "TORSO_ANGLE" for e in self._side_errors)
        new_rep = self._counter.update(landmarks, form_valid=not blocking)

        self._emit(new_rep)

    def on_front_landmarks(self, landmarks) -> None:
        """
        Slot podpięty do PoseWorker kamery PRZEDNIEJ.
        Wykrywa błędy widoczne z przodu (flaring łokci).
        Powtórzenia NIE są liczone z tej kamery (boczna jest dokładniejsza).
        """
        self._front_errors = self._front_analyzer.analyze(landmarks)
        self._emit(new_rep=False)

    def reset(self) -> None:
        """Resetuje licznik i analizatory (np. przy starcie nowego setu)."""
        self._counter.reset()
        self._side_analyzer.reset()
        self._side_errors  = []
        self._front_errors = []

    # ── prywatne ──────────────────────────────────────────────────────────────

    def _emit(self, new_rep: bool) -> None:
        all_errors = self._side_errors + self._front_errors

        result = AnalysisResult(
            reps           = self._counter.reps,
            phase          = self._counter.phase.name,
            errors         = all_errors,
            new_rep        = new_rep,
            calib_progress = self._counter.calib_progress,
        )
        self.stats_updated.emit(result)

        if new_rep:
            self.rep_completed.emit(self._counter.reps)
            # TODO: zapis do bazy danych — self._counter.reps, timestamp, błędy