"""
FormAnalyzer — analiza błędów techniki wiosłowania sztangą.

Dostosowany do opisu:
- prawidłowe pochylenie tułowia ~45°
- łokcie blisko tułowia (kąt ~45°, próg alarmu 60°)
- brak zginania kolan (wypychanie bioder)
- prosty kręgosłup (kąt bark–biodro–kolano >= 85°)
"""

from __future__ import annotations
from dataclasses import dataclass
from collections import deque
import math


@dataclass
class FormError:
    code: str
    message: str
    severity: float  # 0.0–1.0


# Indeksy MediaPipe Pose
_L_SHOULDER = 11
_R_SHOULDER = 12
_L_ELBOW = 13
_R_ELBOW = 14
_L_WRIST = 15
_R_WRIST = 16
_L_HIP = 23
_R_HIP = 24
_L_KNEE = 25
_R_KNEE = 26
_L_ANKLE = 27
_R_ANKLE = 28


def _angle_3pts(a, b, c) -> float:
    """Kąt w stopniach w punkcie b."""
    ax, ay = a.x - b.x, a.y - b.y
    cx, cy = c.x - b.x, c.y - b.y
    dot = ax * cx + ay * cy
    mag = math.hypot(ax, ay) * math.hypot(cx, cy)
    if mag < 1e-6:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / mag))))


class _SmoothFlag:
    """Wygładza bool – True tylko gdy N ostatnich klatek to True."""
    def __init__(self, window: int = 8):
        self._buf = deque(maxlen=window)

    def update(self, value: bool) -> bool:
        self._buf.append(value)
        return len(self._buf) == self._buf.maxlen and all(self._buf)


# ----------------------------------------------------------------------
# Analizator kamery bocznej
# ----------------------------------------------------------------------
class SideFormAnalyzer:
    """
    Błędy z boku:
    1. Zaokrąglone plecy (kąt bark–biodro–kolano < 85°)
    2. Bujanie tułowiem (zmiana kąta > 6°/klatkę)
    3. Zginanie kolan (kolano przesunięte do przodu względem kostki)
    4. Nieprawidłowy kąt pochylenia tułowia (z zakresu 30–60° od pionu)
    """
    ROUNDED_BACK_THRESHOLD = 85.0
    SWINGING_DELTA_THRESHOLD = 6.0
    KNEE_FORWARD_THRESHOLD = 0.05      # norma. różnica x_knee - x_ankle
    MIN_TORSO_ANGLE = 30.0             # stopni od pionu (30° = 60° od podłogi)
    MAX_TORSO_ANGLE = 60.0             # 60° = 30° od podłogi

    def __init__(self):
        self._prev_torso_angle: float | None = None
        self._rounded_flag = _SmoothFlag(window=8)
        self._swinging_flag = _SmoothFlag(window=5)
        self._knee_flag = _SmoothFlag(window=6)
        self._torso_angle_flag = _SmoothFlag(window=10)

    def analyze(self, landmarks) -> list[FormError]:
        errors = []
        lm = landmarks
        try:
            # --- 1. Zaokrąglone plecy ---
            back_angle = _angle_3pts(lm[_R_SHOULDER], lm[_R_HIP], lm[_R_KNEE])
            is_rounded = back_angle < self.ROUNDED_BACK_THRESHOLD
            if self._rounded_flag.update(is_rounded):
                sev = max(0.0, min(1.0, (self.ROUNDED_BACK_THRESHOLD - back_angle) / 20.0))
                errors.append(FormError("ROUNDED_BACK",
                                        "Zaokrąglone plecy! Trzymaj prosty tułów.", sev))

            # --- 2. Bujanie tułowiem (zmiana kąta między klatkami) ---
            torso_dx = lm[_R_SHOULDER].x - lm[_R_HIP].x
            torso_dy = lm[_R_SHOULDER].y - lm[_R_HIP].y
            torso_angle = math.degrees(math.atan2(torso_dx, -torso_dy))  # 0 = pion, 90 = poziomo

            is_swinging = False
            if self._prev_torso_angle is not None:
                delta = abs(torso_angle - self._prev_torso_angle)
                is_swinging = delta > self.SWINGING_DELTA_THRESHOLD
            self._prev_torso_angle = torso_angle
            if self._swinging_flag.update(is_swinging):
                errors.append(FormError("SWINGING", "Bujanie tułowiem! Stabilizuj pozycję.", 0.7))

            # --- 3. Zginanie kolan zamiast wypychania bioder ---
            # Prawa kostka i kolano (lub lewe – symetrycznie)
            knee_offset = lm[_R_KNEE].x - lm[_R_ANKLE].x
            is_knee_forward = knee_offset > self.KNEE_FORWARD_THRESHOLD
            if self._knee_flag.update(is_knee_forward):
                severity = min(1.0, (knee_offset - self.KNEE_FORWARD_THRESHOLD) / 0.1)
                errors.append(FormError("KNEE_FORWARD",
                                        "Zginasz kolana! Wypchnij biodra w tył.", severity))

            # --- 4. Nieprawidłowy kąt pochylenia tułowia (opcjonalnie) ---
            is_bad_angle = torso_angle < self.MIN_TORSO_ANGLE or torso_angle > self.MAX_TORSO_ANGLE
            if self._torso_angle_flag.update(is_bad_angle):
                errors.append(FormError("TORSO_ANGLE",
                                        "Pochyl tułów ~45° (zbyt pionowo lub zbyt nisko).", 0.5))

        except (IndexError, AttributeError):
            pass
        return errors

    def reset(self):
        self._prev_torso_angle = None


# ----------------------------------------------------------------------
# Analizator kamery przedniej
# ----------------------------------------------------------------------
class FrontFormAnalyzer:
    """
    Błędy z przodu:
    - Flaring łokci (kąt bark–łokieć–nadgarstek > 60°)
    """
    ELBOW_FLARE_THRESHOLD = 60.0   # zmienione z 70° na 60° (opis mówi ~45°)

    def __init__(self):
        self._flare_l_flag = _SmoothFlag(window=8)
        self._flare_r_flag = _SmoothFlag(window=8)

    def analyze(self, landmarks) -> list[FormError]:
        errors = []
        lm = landmarks
        try:
            angle_l = _angle_3pts(lm[_L_SHOULDER], lm[_L_ELBOW], lm[_L_WRIST])
            angle_r = _angle_3pts(lm[_R_SHOULDER], lm[_R_ELBOW], lm[_R_WRIST])

            flare_l = angle_l > self.ELBOW_FLARE_THRESHOLD
            flare_r = angle_r > self.ELBOW_FLARE_THRESHOLD

            if self._flare_l_flag.update(flare_l) or self._flare_r_flag.update(flare_r):
                worst = max(angle_l, angle_r)
                severity = min(1.0, (worst - self.ELBOW_FLARE_THRESHOLD) / 30.0)
                errors.append(FormError("ELBOW_FLARE",
                                        "Łokcie za szeroko! Prowadź je blisko ciała.", severity))
        except (IndexError, AttributeError):
            pass
        return errors