"""
FormAnalyzer — analiza błędów techniki wiosłowania sztangą.

Każda metoda zwraca FormError lub None.
Analizator jest podzielony na dwa widoki:
  - SideFormAnalyzer  (kamera boczna)  → zaokrąglone plecy, bujanie tułowiem
  - FrontFormAnalyzer (kamera przednia) → flaring łokci

Błędy są wygładzane czasowo (N kolejnych klatek musi potwierdzić błąd),
żeby unikać fałszywych alarmów przy chwilowych zakłóceniach landmarków.
"""

from __future__ import annotations
from dataclasses import dataclass
from collections import deque
import math


# ── Struktura błędu ───────────────────────────────────────────────────────────

@dataclass
class FormError:
    code:    str    # unikalny identyfikator błędu
    message: str    # czytelny opis dla użytkownika
    severity: float # 0.0–1.0 (jak bardzo zły błąd)


# ── Stałe indeksów MediaPipe Pose ─────────────────────────────────────────────

_L_SHOULDER = 11
_R_SHOULDER = 12
_L_ELBOW    = 13
_R_ELBOW    = 14
_L_WRIST    = 15
_R_WRIST    = 16
_L_HIP      = 23
_R_HIP      = 24


# ── Pomocnicze ────────────────────────────────────────────────────────────────

def _angle_3pts(a, b, c) -> float:
    """Kąt w stopniach w punkcie b, między wektorami b→a i b→c."""
    ax, ay = a.x - b.x, a.y - b.y
    cx, cy = c.x - b.x, c.y - b.y
    dot    = ax * cx + ay * cy
    mag    = math.hypot(ax, ay) * math.hypot(cx, cy)
    if mag < 1e-6:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / mag))))


class _SmoothFlag:
    """
    Wygładza sygnał boolowski: True tylko gdy N ostatnich klatek to True.
    Zapobiega migotaniu błędów przy chwilowych zakłóceniach.
    """
    def __init__(self, window: int = 8):
        self._buf = deque(maxlen=window)

    def update(self, value: bool) -> bool:
        self._buf.append(value)
        return len(self._buf) == self._buf.maxlen and all(self._buf)


# ── Analizator kamery bocznej ─────────────────────────────────────────────────

class SideFormAnalyzer:
    """
    Wykrywa błędy widoczne z boku:
      1. Zaokrąglone plecy — kąt bark–biodro–kolano (sylwetka) < próg
      2. Bujanie tułowiem — zmiana kąta tułowia między klatkami > próg
    """

    # Próg kąta pleców — poniżej tego = zaokrąglone (w stopniach)
    ROUNDED_BACK_THRESHOLD  = 155.0

    # Próg zmiany kąta tułowia między klatkami (stopnie/klatkę) = bujanie
    SWINGING_DELTA_THRESHOLD = 6.0

    def __init__(self):
        self._prev_torso_angle: float | None = None
        self._rounded_flag  = _SmoothFlag(window=8)
        self._swinging_flag = _SmoothFlag(window=5)

    def analyze(self, landmarks) -> list[FormError]:
        errors = []
        lm = landmarks

        try:
            # ── Zaokrąglone plecy ─────────────────────────────────────────
            # Mierzymy kąt: prawy bark → prawy biodro → prawy nadgarstek
            # (przybliżenie kształtu pleców z boku)
            back_angle = _angle_3pts(
                lm[_R_SHOULDER], lm[_R_HIP], lm[_R_WRIST]
            )
            is_rounded = back_angle < self.ROUNDED_BACK_THRESHOLD
            if self._rounded_flag.update(is_rounded):
                severity = max(0.0, min(1.0, (self.ROUNDED_BACK_THRESHOLD - back_angle) / 30.0))
                errors.append(FormError(
                    code="ROUNDED_BACK",
                    message="Zaokrąglone plecy!",
                    severity=severity,
                ))

            # ── Bujanie tułowiem ──────────────────────────────────────────
            # Mierzymy kąt tułowia: bark → biodro (względem pionu)
            torso_dx = lm[_R_SHOULDER].x - lm[_R_HIP].x
            torso_dy = lm[_R_SHOULDER].y - lm[_R_HIP].y
            torso_angle = math.degrees(math.atan2(torso_dx, -torso_dy))

            is_swinging = False
            if self._prev_torso_angle is not None:
                delta = abs(torso_angle - self._prev_torso_angle)
                is_swinging = delta > self.SWINGING_DELTA_THRESHOLD

            self._prev_torso_angle = torso_angle

            if self._swinging_flag.update(is_swinging):
                errors.append(FormError(
                    code="SWINGING",
                    message="Bujanie tułowiem!",
                    severity=0.7,
                ))

        except (IndexError, AttributeError):
            pass

        return errors

    def reset(self):
        self._prev_torso_angle = None


# ── Analizator kamery przedniej ───────────────────────────────────────────────

class FrontFormAnalyzer:
    """
    Wykrywa błędy widoczne z przodu:
      1. Flaring łokci — kąt bark–łokieć–nadgarstek przekracza próg
         (łokcie uciekają za szeroko na boki)
    """

    # Kąt łokcia powyżej którego uznajemy flaring (w stopniach)
    ELBOW_FLARE_THRESHOLD = 70.0

    def __init__(self):
        self._flare_l_flag = _SmoothFlag(window=8)
        self._flare_r_flag = _SmoothFlag(window=8)

    def analyze(self, landmarks) -> list[FormError]:
        errors = []
        lm = landmarks

        try:
            # Kąt lewego łokcia: bark → łokieć → nadgarstek
            angle_l = _angle_3pts(lm[_L_SHOULDER], lm[_L_ELBOW], lm[_L_WRIST])
            angle_r = _angle_3pts(lm[_R_SHOULDER], lm[_R_ELBOW], lm[_R_WRIST])

            # Flaring = łokieć odchodzi za bardzo od tułowia (kąt zbyt duży)
            flare_l = angle_l > self.ELBOW_FLARE_THRESHOLD
            flare_r = angle_r > self.ELBOW_FLARE_THRESHOLD

            if self._flare_l_flag.update(flare_l) or self._flare_r_flag.update(flare_r):
                worst = max(angle_l, angle_r)
                severity = min(1.0, (worst - self.ELBOW_FLARE_THRESHOLD) / 30.0)
                errors.append(FormError(
                    code="ELBOW_FLARE",
                    message="Łokcie za szeroko!",
                    severity=severity,
                ))

        except (IndexError, AttributeError):
            pass

        return errors