"""
app/engine/rowing_analyzer.py
─────────────────────────────
Analiza poprawności ćwiczenia „Wiosłowanie sztangą w opadzie tułowia"
na podstawie landmarków MediaPipe Pose (widok z kamery bocznej).

Sprawdzane kryteria
───────────────────
1. Kąt nachylenia tułowia (biodro→bark vs. poziom)         →  25° – 55°
2. Kąt ugięcia kolan     (biodro–kolano–kostka)             → 140° – 170°
3. Kąt w łokciach        (bark–łokieć–nadgarstek)           → dynamiczny
4. Prostość pleców       (ucho–bark–biodro)                  → ≥ 145°

Integracja z istniejącym kodem
───────────────────────────────
Analizator działa niezależnie od PoseWorker – otrzymuje już obliczone
landmarki (results.pose_landmarks.landmark) i zwraca RowingAnalysis.
Wyniki można wyświetlać nakładką na klatkę z CameraWorker lub jako
komunikaty tekstowe (voice → TTSWorker).

Przykład użycia
───────────────
    analyzer = RowingAnalyzer()

    # w pętli PoseWorker._run():
    if results.pose_landmarks:
        analysis = analyzer.analyze(results.pose_landmarks.landmark)
        if not analysis.visible:
            ...         # za mało landmarków widocznych
        for msg in analysis.issues:
            print(msg)  # lub przekaż do TTSWorker / nakładki na obraz
        print(analysis.angles)   # słownik {nazwa: kąt_w_stopniach}
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Indeksy landmarków MediaPipe Pose
# ---------------------------------------------------------------------------
class _LM:
    LEFT_EAR       = 7
    RIGHT_EAR      = 8
    LEFT_SHOULDER  = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW     = 13
    RIGHT_ELBOW    = 14
    LEFT_WRIST     = 15
    RIGHT_WRIST    = 16
    LEFT_HIP       = 23
    RIGHT_HIP      = 24
    LEFT_KNEE      = 25
    RIGHT_KNEE     = 26
    LEFT_ANKLE     = 27
    RIGHT_ANKLE    = 28


# ---------------------------------------------------------------------------
# Progi kątów (stopnie)
# ---------------------------------------------------------------------------

# Kąt tułowia względem poziomu (linia biodro → bark)
# Prawidłowe wiosłowanie: tułów pochylony ok. 30°–45° od poziomu.
TORSO_ANGLE_MIN  = 25.0   # < MIN → tułów zbyt pionowy
TORSO_ANGLE_MAX  = 55.0   # > MAX → tułów zbyt poziomy (ryzyko lędźwi)

# Kąt w kolanie (biodro–kolano–kostka)
# Lekkie ugięcie – nie blokada, nie przysiad.
KNEE_ANGLE_MIN   = 140.0  # < MIN → kolana zbyt ugięte
KNEE_ANGLE_MAX   = 170.0  # > MAX → kolana zablokowane (brak ugięcia)

# Kąt w łokciu (bark–łokieć–nadgarstek) – progi dla faz ruchu
ELBOW_HANG_MIN   = 150.0  # ≥ MIN → faza zwisu, ramię wyprostowane (OK)
ELBOW_PEAK_MAX   = 100.0  # ≤ MAX → szczyt wiosłowania, dobry skurcz (OK)
ELBOW_ERROR_MAX  =  40.0  # < ERROR → nieprawidłowe, zbyt ostre zagięcie

# Kąt prostości pleców przy barku (ucho–bark–biodro)
# Gdy plecy są proste: linia ucho/bark/biodro ≈ prosta → kąt bliski 180°.
BACK_ANGLE_MIN   = 145.0  # < MIN → zaokrąglenie górnej części pleców


# ---------------------------------------------------------------------------
# Struktury wynikowe
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Wynik pojedynczego sprawdzenia biomechanicznego."""
    name:     str                    # identyfikator sprawdzenia
    ok:       bool                   # czy kryterium spełnione
    angle:    Optional[float]        # zmierzony kąt w stopniach (None = brak danych)
    message:  str                    # komunikat dla użytkownika
    severity: str = "ok"             # "ok" | "warning" | "error"


@dataclass
class RowingAnalysis:
    """
    Zbiorcze wyniki analizy jednej klatki ćwiczenia wiosłowania.

    Atrybuty
    --------
    checks  : lista wyników wszystkich sprawdzeń
    visible : False gdy kluczowe landmarki są zbyt słabo widoczne
    """
    checks:  list[CheckResult] = field(default_factory=list)
    visible: bool = True

    @property
    def all_ok(self) -> bool:
        """True tylko gdy wszystkie sprawdzenia przeszły i ciało jest widoczne."""
        return self.visible and all(c.ok for c in self.checks)

    @property
    def issues(self) -> list[str]:
        """Lista komunikatów tylko dla nieprawidłowych sprawdzeń."""
        return [c.message for c in self.checks if not c.ok]

    @property
    def angles(self) -> dict[str, float]:
        """Słownik {nazwa: kąt_stopnie} dla wszystkich sprawdzeń z dostępnym kątem."""
        return {c.name: c.angle for c in self.checks if c.angle is not None}

    @property
    def errors(self) -> list[CheckResult]:
        """Tylko sprawdzenia z severity == 'error'."""
        return [c for c in self.checks if c.severity == "error"]

    @property
    def warnings(self) -> list[CheckResult]:
        """Tylko sprawdzenia z severity == 'warning'."""
        return [c for c in self.checks if c.severity == "warning"]


# ---------------------------------------------------------------------------
# Funkcje geometryczne
# ---------------------------------------------------------------------------

def _vec2(a: Any, b: Any) -> tuple[float, float]:
    """Wektor 2D (płaszczyzna XY normalizowana MediaPipe) od punktu a do b."""
    return (b.x - a.x, b.y - a.y)


def _angle_between_vecs(v1: tuple[float, float], v2: tuple[float, float]) -> float:
    """Kąt (stopnie) między dwoma wektorami 2D; wynik w przedziale [0°, 180°]."""
    dot   = v1[0] * v2[0] + v1[1] * v2[1]
    mag1  = math.hypot(*v1)
    mag2  = math.hypot(*v2)
    if mag1 < 1e-9 or mag2 < 1e-9:
        return 0.0
    cos_a = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_a))


def _joint_angle(a: Any, b: Any, c: Any) -> float:
    """
    Kąt w stopniach przy wierzchołku b w trójkącie a–b–c.
    Punkty to obiekty NormalizedLandmark z polami .x, .y.
    Wynik w przedziale [0°, 180°].
    """
    return _angle_between_vecs(_vec2(b, a), _vec2(b, c))


def _angle_from_horizontal(a: Any, b: Any) -> float:
    """
    Kąt (stopnie) jaki tworzy wektor a→b z osią poziomą.
    Wynik zawsze w przedziale [0°, 90°].
    Używane do pomiaru nachylenia tułowia.
    """
    dx = b.x - a.x
    dy = b.y - a.y   # w układzie ekranowym y rośnie ku dołowi
    return math.degrees(math.atan2(abs(dy), abs(dx)))


# ---------------------------------------------------------------------------
# Główna klasa analizatora
# ---------------------------------------------------------------------------

class RowingAnalyzer:
    """
    Analizuje poprawność „Wiosłowania sztangą w opadzie tułowia"
    na podstawie jednej klatki landmarków MediaPipe Pose.

    Zaprojektowany dla kamery bocznej – do ćwiczącego widzi się z profilu,
    co pozwala ocenić kąty tułowia, kolan, łokci i krzywizny pleców.

    Analizator automatycznie wybiera lepiej widoczną stronę ciała.
    """

    # Minimalna widoczność landmarku MediaPipe (0–1)
    # Poniżej progu landmark jest pomijany / zwracane jest visible=False
    VISIBILITY_THRESHOLD = 0.50

    # -----------------------------------------------------------------------
    # Główna metoda
    # -----------------------------------------------------------------------

    def analyze(self, landmarks) -> RowingAnalysis:
        """
        Analizuje landmarki jednej klatki i zwraca RowingAnalysis.

        Parametry
        ---------
        landmarks : sekwencja NormalizedLandmark (results.pose_landmarks.landmark)

        Zwraca
        ------
        RowingAnalysis z listą CheckResult i podsumowaniem stanu formy.
        Gdy visible=False brakuje danych (np. osoba poza kadrem).
        """
        lm = landmarks

        # Wybierz stronę ciała lepiej widoczną z kamery bocznej
        side = self._dominant_side(lm)

        # Pobierz landmarki po wybranej stronie
        ear      = lm[_LM.LEFT_EAR      if side == "left" else _LM.RIGHT_EAR]
        shoulder = lm[_LM.LEFT_SHOULDER if side == "left" else _LM.RIGHT_SHOULDER]
        elbow    = lm[_LM.LEFT_ELBOW    if side == "left" else _LM.RIGHT_ELBOW]
        wrist    = lm[_LM.LEFT_WRIST    if side == "left" else _LM.RIGHT_WRIST]
        hip      = lm[_LM.LEFT_HIP      if side == "left" else _LM.RIGHT_HIP]
        knee     = lm[_LM.LEFT_KNEE     if side == "left" else _LM.RIGHT_KNEE]
        ankle    = lm[_LM.LEFT_ANKLE    if side == "left" else _LM.RIGHT_ANKLE]

        # Sprawdź minimalną widoczność kluczowych punktów (bez ucha – opcjonalne)
        key_landmarks = [shoulder, elbow, wrist, hip, knee, ankle]
        if any(p.visibility < self.VISIBILITY_THRESHOLD for p in key_landmarks):
            return RowingAnalysis(visible=False)

        # Wykonaj wszystkie sprawdzenia
        checks: list[CheckResult] = [
            self._check_torso_angle(hip, shoulder),
            self._check_knee_angle(hip, knee, ankle),
            self._check_elbow_angle(shoulder, elbow, wrist),
            self._check_back_straightness(ear, shoulder, hip),
        ]

        return RowingAnalysis(checks=checks)

    # -----------------------------------------------------------------------
    # Wybór dominującej strony ciała
    # -----------------------------------------------------------------------

    def _dominant_side(self, lm) -> str:
        """
        Zwraca 'left' lub 'right' w zależności od tego, która strona ciała
        jest lepiej widoczna w kadrze (suma widoczności kluczowych landmarków).
        """
        left_vis  = (lm[_LM.LEFT_SHOULDER].visibility  +
                     lm[_LM.LEFT_HIP].visibility        +
                     lm[_LM.LEFT_KNEE].visibility       +
                     lm[_LM.LEFT_ELBOW].visibility)
        right_vis = (lm[_LM.RIGHT_SHOULDER].visibility  +
                     lm[_LM.RIGHT_HIP].visibility       +
                     lm[_LM.RIGHT_KNEE].visibility      +
                     lm[_LM.RIGHT_ELBOW].visibility)
        return "left" if left_vis >= right_vis else "right"

    # -----------------------------------------------------------------------
    # Sprawdzenie 1 – Kąt nachylenia tułowia
    # -----------------------------------------------------------------------

    def _check_torso_angle(self, hip: Any, shoulder: Any) -> CheckResult:
        """
        Mierzy kąt jaki linia biodro→bark tworzy z poziomem.

        Prawidłowe wiosłowanie w opadzie: tułów pochylony ok. 30°–45°,
        co daje dobry zakres ruchu łopatki i aktywację mięśni grzbietu.

        Zbyt pionowo (> 55°) → ćwiczenie przypomina stojące wiosłowanie,
                                traci się zalety pozycji pochylonej.
        Zbyt poziomo (< 25°) → nadmierne obciążenie odcinka lędźwiowego
                                i trudność utrzymania napięcia core.
        """
        angle = _angle_from_horizontal(hip, shoulder)

        if angle < TORSO_ANGLE_MIN:
            return CheckResult(
                name="torso_angle",
                ok=False,
                angle=angle,
                message=(
                    f"Tułów zbyt pionowy ({angle:.0f}°). "
                    "Pochyl się bardziej do przodu — tułów powinien tworzyć "
                    "ok. 30°–45° z podłożem."
                ),
                severity="error",
            )
        if angle > TORSO_ANGLE_MAX:
            return CheckResult(
                name="torso_angle",
                ok=False,
                angle=angle,
                message=(
                    f"Tułów zbyt poziomy ({angle:.0f}°). "
                    "Unieś lekko tułów — zbyt duże pochylenie "
                    "przeciąża dolny odcinek kręgosłupa."
                ),
                severity="warning",
            )
        return CheckResult(
            name="torso_angle",
            ok=True,
            angle=angle,
            message=f"Kąt nachylenia tułowia prawidłowy ({angle:.0f}°). ✓",
            severity="ok",
        )

    # -----------------------------------------------------------------------
    # Sprawdzenie 2 – Kąt ugięcia kolan
    # -----------------------------------------------------------------------

    def _check_knee_angle(self, hip: Any, knee: Any, ankle: Any) -> CheckResult:
        """
        Mierzy kąt przy kolanie (biodro–kolano–kostka).

        Lekkie ugięcie kolan (140°–170°) stabilizuje pozycję,
        odciąża dolny odcinek kręgosłupa i chroni stawy kolanowe.

        Zbyt ugięte (< 140°) → pozycja przypomina przysiad,
                                traci efekt izolacji grzbietu.
        Zablokowane (> 170°) → brak naturalnego ugięcia, ryzyko
                                przeniesienia siły na kolana.
        """
        angle = _joint_angle(hip, knee, ankle)

        if angle < KNEE_ANGLE_MIN:
            return CheckResult(
                name="knee_angle",
                ok=False,
                angle=angle,
                message=(
                    f"Kolana zbyt ugięte ({angle:.0f}°). "
                    "Wyprostuj lekko nogi — to wiosłowanie w opadzie, "
                    "nie przysiad."
                ),
                severity="warning",
            )
        if angle > KNEE_ANGLE_MAX:
            return CheckResult(
                name="knee_angle",
                ok=False,
                angle=angle,
                message=(
                    f"Kolana prawie wyprostowane ({angle:.0f}°). "
                    "Ugnij lekko kolana, aby odciążyć stawy "
                    "kolanowe i ustabilizować kręgosłup."
                ),
                severity="warning",
            )
        return CheckResult(
            name="knee_angle",
            ok=True,
            angle=angle,
            message=f"Ugięcie kolan prawidłowe ({angle:.0f}°). ✓",
            severity="ok",
        )

    # -----------------------------------------------------------------------
    # Sprawdzenie 3 – Kąt w łokciach (dynamiczny)
    # -----------------------------------------------------------------------

    def _check_elbow_angle(
        self, shoulder: Any, elbow: Any, wrist: Any
    ) -> CheckResult:
        """
        Mierzy kąt przy łokciu (bark–łokieć–nadgarstek) z uwzględnieniem fazy ruchu.

        Fazy wiosłowania:
        ─────────────────
        • Zwis / pozycja wyjściowa  → kąt ≥ 150° (ramię prawie wyprostowane)
        • Ruch w górę / w dół       → kąt 100°–150° (przejście – ruch trwa)
        • Szczyt wiosłowania        → kąt ≤ 100° (łokieć za linią pleców)

        Błąd: kąt < 40° → nieprawidłowe, bardzo ostre zagięcie łokcia,
        może wskazywać na zły chwyt lub ruch compensacyjny.
        """
        angle = _joint_angle(shoulder, elbow, wrist)

        if angle < ELBOW_ERROR_MAX:
            return CheckResult(
                name="elbow_angle",
                ok=False,
                angle=angle,
                message=(
                    f"Łokieć zbyt mocno zagięty ({angle:.0f}°). "
                    "Sprawdź chwyt i tor ruchu — ramię nie powinno "
                    "być tak bardzo złożone."
                ),
                severity="error",
            )

        if angle >= ELBOW_HANG_MIN:
            # Faza zwisu – ramię wyprostowane, pozycja wyjściowa lub końcowa
            return CheckResult(
                name="elbow_angle",
                ok=True,
                angle=angle,
                message=(
                    f"Ramiona wyprostowane — faza zwisu ({angle:.0f}°). ✓ "
                    "Pamiętaj, by na starcie ramiona były w pełni rozciągnięte."
                ),
                severity="ok",
            )

        if angle <= ELBOW_PEAK_MAX:
            # Szczyt wiosłowania – dobry skurcz, łokcie za plecami
            return CheckResult(
                name="elbow_angle",
                ok=True,
                angle=angle,
                message=(
                    f"Szczyt wiosłowania — łokcie cofnięte ({angle:.0f}°). ✓ "
                    "Utrzymaj skurcz przez chwilę przed opuszczeniem."
                ),
                severity="ok",
            )

        # Kąt przejściowy 100°–150° – ruch w toku
        return CheckResult(
            name="elbow_angle",
            ok=True,
            angle=angle,
            message=f"Ruch w toku — kąt łokcia ({angle:.0f}°).",
            severity="ok",
        )

    # -----------------------------------------------------------------------
    # Sprawdzenie 4 – Prostość pleców (kąt ucho–bark–biodro)
    # -----------------------------------------------------------------------

    def _check_back_straightness(
        self, ear: Any, shoulder: Any, hip: Any
    ) -> CheckResult:
        """
        Ocenia prostość pleców mierząc kąt przy barku w trójkącie ucho–bark–biodro.

        Gdy kręgosłup jest w pozycji neutralnej, ucho / głowa, bark i biodro
        tworzą w przybliżeniu prostą linię → kąt przy barku ≈ 160°–180°.

        Garbienie (zaokrąglenie górnych pleców) powoduje, że bark wysuwa się
        do przodu i ku dołowi względem linii ucho–biodro → kąt MALEJE.

        Próg BACK_ANGLE_MIN = 145° to granica tolerancji; poniżej należy
        ściągnąć łopatki i unieść klatkę piersiową.

        Uwaga: widoczność ucha jest opcjonalna — jeśli MediaPipe nie widzi
        ucha z dostateczną pewnością, sprawdzenie jest pomijane.
        """
        if ear.visibility < self.VISIBILITY_THRESHOLD:
            return CheckResult(
                name="back_straightness",
                ok=True,
                angle=None,
                message="Prostość pleców: brak danych (ucho poza kadrem).",
                severity="ok",
            )

        angle = _joint_angle(ear, shoulder, hip)

        if angle < BACK_ANGLE_MIN:
            return CheckResult(
                name="back_straightness",
                ok=False,
                angle=angle,
                message=(
                    f"Wykryto zaokrąglenie górnych pleców ({angle:.0f}°). "
                    "Ściągnij łopatki ku sobie, unieś klatkę piersiową "
                    "i utrzymaj neutralny kręgosłup — plecy proste jak deska."
                ),
                severity="error",
            )

        return CheckResult(
            name="back_straightness",
            ok=True,
            angle=angle,
            message=f"Plecy utrzymane w neutralnej pozycji ({angle:.0f}°). ✓",
            severity="ok",
        )