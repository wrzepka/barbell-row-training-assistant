"""
RepCounter — licznik powtórzeń wiosłowania sztangą.

Algorytm (kamera boczna lub przednia):
  Śledzimy pozycję Y nadgarstka dominującej ręki względem biodra.
  Gdy nadgarstek idzie w górę (faza koncentryczna) i przekroczy próg,
  a następnie opada z powrotem (faza ekscentryczna) — liczymy jedno powtórzenie.

  Progi są względne (% odległości bark–biodro), więc działają niezależnie
  od rozdzielczości kamery i odległości od obiektywu.
"""

from enum import Enum, auto


class Phase(Enum):
    IDLE = auto()  # oczekiwanie na start
    PULLING = auto()  # faza koncentryczna (nadgarstek idzie w górę)
    LOWERING = auto()  # faza ekscentryczna (nadgarstek opada)


class RepCounter:
    """
    Stateless-ish licznik powtórzeń.
    Wywołuj update() dla każdej klatki z landmarkami MediaPipe.

    Parametry
    ---------
    pull_threshold : float
        Jak wysoko (względnie) nadgarstek musi wznieść się względem biodra,
        żeby uznać fazę koncentryczną za zakończoną. 0.35 = 35% odległości bark–biodro.
    return_threshold : float
        Jak nisko nadgarstek musi wrócić, żeby uznać powtórzenie za kompletne.
    """

    # Indeksy landmarków MediaPipe Pose
    _L_SHOULDER = 11
    _R_SHOULDER = 12
    _L_HIP = 23
    _R_HIP = 24
    _L_WRIST = 15
    _R_WRIST = 16

    def __init__(self, pull_threshold: float = 0.35, return_threshold: float = 0.15):
        self.pull_threshold = pull_threshold
        self.return_threshold = return_threshold

        self._reps = 0
        self._phase = Phase.IDLE

    # ── publiczne API ─────────────────────────────────────────────────────────

    @property
    def reps(self) -> int:
        return self._reps

    @property
    def phase(self) -> Phase:
        return self._phase

    def reset(self):
        self._reps = 0
        self._phase = Phase.IDLE

    def update(self, landmarks) -> bool:
        """
        Przetwarza jedną klatkę landmarków.

        :param landmarks: lista landmarks z results.pose_landmarks.landmark (MediaPipe)
        :returns: True jeśli właśnie zaliczono nowe powtórzenie
        """
        ratio = self._wrist_ratio(landmarks)
        if ratio is None:
            return False

        new_rep = False

        if self._phase == Phase.IDLE:
            # Czekamy aż nadgarstek zejdzie nisko (pozycja startowa)
            if ratio < self.return_threshold:
                self._phase = Phase.PULLING

        elif self._phase == Phase.PULLING:
            # Czekamy na pełne podciągnięcie
            if ratio >= self.pull_threshold:
                self._phase = Phase.LOWERING

        elif self._phase == Phase.LOWERING:
            # Czekamy na powrót do pozycji startowej
            if ratio < self.return_threshold:
                self._reps += 1
                self._phase = Phase.PULLING
                new_rep = True

        return new_rep

    # ── obliczenia ────────────────────────────────────────────────────────────

    def _wrist_ratio(self, landmarks) -> float | None:
        """
        Oblicza znormalizowaną pozycję nadgarstka.

        Zwraca: (hip_y - wrist_y) / shoulder_to_hip_dist
        Wartość > 0 oznacza że nadgarstek jest powyżej biodra.
        Im wyżej tym większa wartość.
        """
        try:
            l = landmarks

            # Używamy prawej strony (dominująca dla wiosłowania — można sparametryzować)
            shoulder_y = l[self._R_SHOULDER].y
            hip_y = l[self._R_HIP].y
            wrist_y = l[self._R_WRIST].y

            dist = abs(hip_y - shoulder_y)
            if dist < 1e-6:
                return None

            # Wartość dodatnia = nadgarstek powyżej biodra
            ratio = (hip_y - wrist_y) / dist
            return float(ratio)

        except (IndexError, AttributeError):
            return None
