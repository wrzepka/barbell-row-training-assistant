"""
RepCounter — licznik powtórzeń wiosłowania sztangą.

Algorytm (kamera boczna lub przednia):
  Śledzimy pozycję Y nadgarstków OBU rąk względem bioder.
  Gdy nadgarstki idą w górę (faza koncentryczna) i przekroczą próg,
  a następnie opadają z powrotem (faza ekscentryczna) — liczymy jedno powtórzenie.

  Progi są względne (% odległości bark–biodro), więc działają niezależnie
  od rozdzielczości kamery i odległości od obiektywu.
"""

from enum import Enum, auto


class Phase(Enum):
    IDLE = auto()  # oczekiwanie na start
    PULLING = auto()  # faza koncentryczna (nadgarstki idą w górę)
    LOWERING = auto()  # faza ekscentryczna (nadgarstki opadają)


class RepCounter:
    """
    Stateless-ish licznik powtórzeń.
    Wywołuj update() dla każdej klatki z landmarkami MediaPipe.
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
            # Czekamy aż nadgarstki zejdą nisko (pozycja startowa)
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
        Oblicza znormalizowaną pozycję nadgarstków dla OBU stron ciała
        i zwraca ich wartość uśrednioną, pod warunkiem że ruch jest symetryczny.
        """
        try:
            l = landmarks

            # 1. Strona prawa
            r_shoulder_y = l[self._R_SHOULDER].y
            r_hip_y = l[self._R_HIP].y
            r_wrist_y = l[self._R_WRIST].y
            r_dist = abs(r_hip_y - r_shoulder_y)

            # 2. Strona lewa
            l_shoulder_y = l[self._L_SHOULDER].y
            l_hip_y = l[self._L_HIP].y
            l_wrist_y = l[self._L_WRIST].y
            l_dist = abs(l_hip_y - l_shoulder_y)

            if r_dist < 1e-6 or l_dist < 1e-6:
                return None

            # Obliczamy ratio dla obu rąk osobno
            r_ratio = (r_hip_y - r_wrist_y) / r_dist
            l_ratio = (l_hip_y - l_wrist_y) / l_dist

            # ZABEZPIECZENIE: Jeśli różnica wysokości między nadgarstkami
            # jest zbyt duża (np. ktoś podniósł tylko jedną rękę), ignorujemy ruch.
            if abs(r_ratio - l_ratio) > 0.20:
                return None

            # Zwracamy średnią wartość dla obu rąk
            return float((r_ratio + l_ratio) / 2.0)

        except (IndexError, AttributeError):
            return None