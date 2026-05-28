"""
RepCounter — licznik powtórzeń wiosłowania sztangą.

Ratio = (wrist_y - shoulder_y) / (hip_y - shoulder_y)

Wartości zmierzone empirycznie:
  ~0.6–0.7  szczyt ruchu  (nadgarstki przy klatce)
  ~1.2–1.4  dół           (nadgarstki opuszczone poniżej bioder)

Maszyna stanów:
  IDLE     → PULLING  gdy ratio >= return_threshold  (ręce na dole)
  PULLING  → TOP      gdy ratio <= pull_threshold    (ręce na górze) → tu +1 rep
  TOP      → LOWERING gdy ratio > pull_threshold
  LOWERING → PULLING  gdy ratio >= return_threshold  (gotowy na kolejny)
"""

from __future__ import annotations
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)


class Phase(Enum):
    IDLE     = auto()
    PULLING  = auto()
    TOP      = auto()
    LOWERING = auto()


class RepCounter:
    _R_SHOULDER = 12
    _R_HIP      = 24
    _R_WRIST    = 16

    def __init__(
        self,
        pull_threshold:   float = 0.75,   # poniżej tego = ręce na górze (rep!)
        return_threshold: float = 1.10,   # powyżej tego = ręce na dole (start)
        debug:            bool  = False,
    ):
        self.pull_threshold   = pull_threshold
        self.return_threshold = return_threshold
        self.debug            = debug

        self._reps             = 0
        self._phase            = Phase.IDLE
        self._form_ok_this_rep = True

    @property
    def reps(self) -> int:
        return self._reps

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def calib_progress(self) -> float:
        return 1.0   # brak kalibracji — zawsze gotowy

    def reset(self) -> None:
        self._reps             = 0
        self._phase            = Phase.IDLE
        self._form_ok_this_rep = True

    def update(self, landmarks, form_valid: bool = True) -> bool:
        ratio = self._wrist_ratio(landmarks)
        if ratio is None:
            return False

        if self.debug:
            logger.debug("ratio=%.3f  phase=%-8s  form=%s", ratio, self._phase.name, form_valid)

        return self._fsm(ratio, form_valid)

    def _fsm(self, ratio: float, form_valid: bool) -> bool:
        new_rep = False

        if self._phase == Phase.IDLE:
            if ratio >= self.return_threshold:
                self._phase            = Phase.PULLING
                self._form_ok_this_rep = True
                if self.debug:
                    logger.debug("→ PULLING")

        elif self._phase == Phase.PULLING:
            if not form_valid:
                self._form_ok_this_rep = False
            if ratio <= self.pull_threshold:
                self._phase = Phase.TOP
                if self._form_ok_this_rep:
                    self._reps += 1
                    new_rep = True
                    if self.debug:
                        logger.debug("✓ REP %d  ratio=%.3f", self._reps, ratio)
                elif self.debug:
                    logger.debug("✗ odrzucony (forma)")

        elif self._phase == Phase.TOP:
            if ratio > self.pull_threshold:
                self._phase = Phase.LOWERING
                if self.debug:
                    logger.debug("→ LOWERING")

        elif self._phase == Phase.LOWERING:
            if ratio >= self.return_threshold:
                self._phase            = Phase.PULLING
                self._form_ok_this_rep = True
                if self.debug:
                    logger.debug("→ PULLING (kolejny)")

        return new_rep

    def _wrist_ratio(self, landmarks) -> float | None:
        try:
            lm   = landmarks
            s_y  = lm[self._R_SHOULDER].y
            h_y  = lm[self._R_HIP].y
            w_y  = lm[self._R_WRIST].y
            dist = abs(h_y - s_y)
            if dist < 1e-6:
                return None
            return (w_y - s_y) / dist
        except (IndexError, AttributeError):
            return None