"""
RepCounter — licznik powtórzeń wiosłowania sztangą.

Metryka: kąt w stawie łokciowym (bark–łokieć–nadgarstek).
  ~170–180°  ręce wyprostowane (dół ruchu, pozycja startowa)
  ~30–70°    ręce ugięte, sztanga przy klatce (góra ruchu)

Maszyna stanów:
  IDLE     → PULLING  gdy angle >= return_threshold  (ręce wyprostowane)
  PULLING  → TOP      gdy angle <= pull_threshold     (ręce ugięte)        → tu +1 rep
  TOP      → LOWERING gdy angle > pull_threshold
  LOWERING → PULLING  gdy angle >= return_threshold  (gotowy na kolejny)
"""

from __future__ import annotations
import logging
import math
from enum import Enum, auto

logger = logging.getLogger(__name__)


class Phase(Enum):
    IDLE     = auto()
    PULLING  = auto()
    TOP      = auto()
    LOWERING = auto()


class RepCounter:
    _R_SHOULDER = 12
    _R_ELBOW    = 14
    _R_WRIST    = 16

    def __init__(
        self,
        pull_threshold:   float = 70.0,    # poniżej tego (stopnie) = łokieć ugięty, ręce na górze (rep!)
        return_threshold: float = 150.0,   # powyżej tego (stopnie) = ręce wyprostowane (start)
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
        angle = self._elbow_angle(landmarks)
        if angle is None:
            return False

        if self.debug:
            logger.debug("angle=%.1f°  phase=%-8s  form=%s", angle, self._phase.name, form_valid)

        return self._fsm(angle, form_valid)

    def _fsm(self, angle: float, form_valid: bool) -> bool:
        new_rep = False

        if self._phase == Phase.IDLE:
            if angle >= self.return_threshold:
                self._phase            = Phase.PULLING
                self._form_ok_this_rep = True
                if self.debug:
                    logger.debug("→ PULLING")

        elif self._phase == Phase.PULLING:
            if not form_valid:
                self._form_ok_this_rep = False
            if angle <= self.pull_threshold:
                self._phase = Phase.TOP
                if self._form_ok_this_rep:
                    self._reps += 1
                    new_rep = True
                    if self.debug:
                        logger.debug("✓ REP %d  angle=%.1f°", self._reps, angle)
                elif self.debug:
                    logger.debug("✗ odrzucony (forma)")

        elif self._phase == Phase.TOP:
            if angle > self.pull_threshold:
                self._phase = Phase.LOWERING
                if self.debug:
                    logger.debug("→ LOWERING")

        elif self._phase == Phase.LOWERING:
            if angle >= self.return_threshold:
                self._phase            = Phase.PULLING
                self._form_ok_this_rep = True
                if self.debug:
                    logger.debug("→ PULLING (kolejny)")

        return new_rep

    def _elbow_angle(self, landmarks) -> float | None:
        """Kąt w stawie łokciowym (bark–łokieć–nadgarstek), w stopniach.

        180° = ręka całkowicie wyprostowana, mniejsze wartości = ugięty łokieć.
        Liczony z wektorów 2D (x, y) z punktu łokcia do barku i do nadgarstka,
        więc jest niezależny od kąta pochylenia tułowia.
        """
        try:
            lm = landmarks
            s  = lm[self._R_SHOULDER]
            e  = lm[self._R_ELBOW]
            w  = lm[self._R_WRIST]

            v1 = (s.x - e.x, s.y - e.y)
            v2 = (w.x - e.x, w.y - e.y)

            mag1 = math.hypot(*v1)
            mag2 = math.hypot(*v2)
            if mag1 < 1e-6 or mag2 < 1e-6:
                return None

            cos_angle = (v1[0] * v2[0] + v1[1] * v2[1]) / (mag1 * mag2)
            cos_angle = max(-1.0, min(1.0, cos_angle))
            return math.degrees(math.acos(cos_angle))
        except (IndexError, AttributeError):
            return None