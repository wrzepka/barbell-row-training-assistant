"""
Moduł widoku historii treningów.

Zawiera:
- HistoryCard – rozwijany kafelek pojedynczego treningu,
- PerformanceChart – wykres liniowy postępu wyników,
- StatsSummary – blok statystyk ogólnych,
- HistoryView – główny widget składający lewą listę i prawy panel.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis
from PySide6.QtGui import QPainter, QColor

from app.const import ScreenModes
from app.ui.skeleton_history_view import SkeletonHistoryView

# TODO: Docelowo dane będą pobierane z bazy danych (np. SQLite, PostgreSQL).
#       Poniższe MOCK_DATA służy tylko do testów wizualnych i zostanie zastąpione.
MOCK_DATA = [
    {"date": "2024-05-15 14:30", "sets": 3, "reps": "12", "weight": "60kg", "duration": "18 min", "score": 95, "to_fix": ["Brak uwag"]},
    {"date": "2024-05-14 10:15", "sets": 4, "reps": "10", "weight": "60kg", "duration": "22 min", "score": 65,
     "to_fix": ["Wyprostuj plecy!", "Zwolnij ruch"]},
    {"date": "2024-05-12 18:00", "sets": 3, "reps": "12", "weight": "55kg", "duration": "20 min", "score": 88, "to_fix": ["Głowa w dół"]},
    {"date": "2024-05-10 09:00", "sets": 4, "reps": "8", "weight": "50kg", "duration": "16 min", "score": 92, "to_fix": ["Brak uwag"]},
    {"date": "2024-05-08 16:20", "sets": 3, "reps": "10", "weight": "55kg", "duration": "19 min", "score": 75,
     "to_fix": ["Prowadź łokcie bliżej ciała"]},
    {"date": "2024-05-06 12:45", "sets": 4, "reps": "12", "weight": "50kg", "duration": "21 min", "score": 81,
     "to_fix": ["Kontroluj fazę negatywną"]},
    {"date": "2024-05-04 19:30", "sets": 3, "reps": "10", "weight": "45kg", "duration": "17 min", "score": 98, "to_fix": ["Brak uwag"]},
    {"date": "2024-05-02 08:15", "sets": 4, "reps": "15", "weight": "40kg", "duration": "25 min", "score": 60,
     "to_fix": ["Zmniejsz ciężar", "Pilnuj lędźwi"]},
    {"date": "2024-04-30 17:00", "sets": 3, "reps": "10", "weight": "50kg", "duration": "18 min", "score": 87, "to_fix": ["Brak uwag"]},
    {"date": "2024-04-28 11:10", "sets": 4, "reps": "12", "weight": "50kg", "duration": "20 min", "score": 91, "to_fix": ["Brak uwag"]},
]

# Dane dla wykresu – od najstarszego do najnowszego (kolejność postępu)
CHART_DATA = list(reversed(MOCK_DATA))


class HistoryCard(QFrame):
    """
    Kafelek pojedynczego treningu.

    Po kliknięciu rozwija się, pokazując szczegółowe uwagi do analizy postawy.
    Zawiera animację rozwijania.
    """

    def __init__(self, data):
        super().__init__()
        self.setObjectName("historyCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("expanded", "false")

        self._setup_ui(data)

    def _setup_ui(self, data):
        """Buduje strukturę kafelka (nagłówek + rozwijane detale)."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 15, 20, 15)
        self.main_layout.setSpacing(0)

        # Nagłówek (widoczny zawsze)
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        txt_box = QVBoxLayout()
        d_lbl = QLabel(data["date"])
        d_lbl.setObjectName("dateLabel")
        ex_lbl = QLabel("Wiosłowanie sztangą")
        ex_lbl.setObjectName("exerciseName")
        txt_box.addWidget(d_lbl)
        txt_box.addWidget(ex_lbl)

        stats_lbl = QLabel(f"{data['weight']} | {data['reps']} powt. | {data['sets']} serie | {data['duration']}")
        stats_lbl.setObjectName("statsLabel")

        score_val = QLabel(f"{data['score']}%")
        score_val.setObjectName("scoreLabel")
        score_val.setProperty("class", "scoreHigh" if data['score'] > 80 else "scoreLow")

        self.arrow = QLabel("▼")
        self.arrow.setObjectName("arrowLabel")

        header_layout.addLayout(txt_box, 2)
        header_layout.addWidget(stats_lbl, 1, Qt.AlignCenter)
        header_layout.addWidget(score_val, 0, Qt.AlignRight)
        header_layout.addWidget(self.arrow, 0, Qt.AlignRight)

        # Detale (rozwijana część)
        self.details_widget = QWidget()
        self.details_widget.setObjectName("detailsWidget")
        self.details_widget.setMaximumHeight(0)

        det_layout = QVBoxLayout(self.details_widget)
        det_layout.setContentsMargins(0, 15, 0, 0)

        line = QFrame()
        line.setObjectName("separator")
        det_layout.addWidget(line)

        fix_title = QLabel("UWAGI Z ANALIZY POSTAWY:")
        fix_title.setObjectName("fixTitle")
        det_layout.addWidget(fix_title)

        for item in data["to_fix"]:
            b_lbl = QLabel(f"• {item}")
            b_lbl.setObjectName("bulletLabel")
            det_layout.addWidget(b_lbl)

        self.main_layout.addWidget(self.header_widget)
        self.main_layout.addWidget(self.details_widget)

        # Animacja
        self.anim = QPropertyAnimation(self.details_widget, b"maximumHeight")
        self.anim.setDuration(350)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)

    def mousePressEvent(self, event):
        """Obsługa kliknięcia – rozwija / zwija kafelek."""
        if event.button() == Qt.LeftButton:
            is_opening = self.details_widget.maximumHeight() == 0
            h = self.details_widget.layout().sizeHint().height()

            self.anim.setStartValue(0 if is_opening else h)
            self.anim.setEndValue(h if is_opening else 0)
            self.arrow.setText("▲" if is_opening else "▼")
            self.setProperty("expanded", "true" if is_opening else "false")

            self.style().unpolish(self)
            self.style().polish(self)
            self.anim.start()


class PerformanceChart(QWidget):
    """Widget z wykresem liniowym postępu wyników w czasie."""

    def __init__(self, data):
        super().__init__()
        self.data = data
        self._setup_chart()

    def _setup_chart(self):
        series = QLineSeries()
        for i, record in enumerate(self.data):
            series.append(i, record["score"])

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Postęp wyników (%)")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#2a2a2a"))
        chart.setTitleBrush(QColor("white"))
        chart.setPlotAreaBackgroundBrush(QColor("#1e1e1e"))
        chart.setPlotAreaBackgroundVisible(True)

        # Oś X z datami
        axis_x = QCategoryAxis()
        axis_x.setLabelsColor(QColor("#aaaaaa"))
        axis_x.setTitleText("Trening (od najstarszego)")
        axis_x.setTitleBrush(QColor("white"))
        for i, record in enumerate(self.data):
            if i % 2 == 0:
                short_date = record["date"][5:10]  # MM-DD
                axis_x.append(short_date, i)
        axis_x.setRange(0, len(self.data) - 1)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # Oś Y
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Wynik (%)")
        axis_y.setTitleBrush(QColor("white"))
        axis_y.setLabelsColor(QColor("#aaaaaa"))
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        pen = series.pen()
        pen.setColor(QColor("#adff2f"))
        pen.setWidth(2)
        series.setPen(pen)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(chart_view)


class StatsSummary(QWidget):
    """Dolny blok statystyk ogólnych – style w globalnym QSS."""

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setObjectName("statsSummary")
        self._setup_ui()

    def _setup_ui(self):
        total_trainings = len(self.data)
        avg_score = sum(d["score"] for d in self.data) / total_trainings
        best_score = max(d["score"] for d in self.data)
        worst_score = min(d["score"] for d in self.data)

        all_notes = [note for d in self.data for note in d["to_fix"] if note != "Brak uwag"]
        most_common_note = max(set(all_notes), key=all_notes.count) if all_notes else "Brak krytycznych uwag"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title = QLabel("PODSUMOWANIE OGÓLNE")
        title.setObjectName("statsTitle")
        layout.addWidget(title)

        stats = [
            f"Łączna liczba treningów: {total_trainings}",
            f"Średni wynik: {avg_score:.1f}%",
            f"Najlepszy wynik: {best_score}%",
            f"Najsłabszy wynik: {worst_score}%",
            f"Najczęstsza uwaga: {most_common_note}"
        ]

        for stat in stats:
            lbl = QLabel(stat)
            lbl.setObjectName("statsLine")
            layout.addWidget(lbl)

        layout.addStretch()


class HistoryView(QWidget):
    """
    Główny widok historii treningów.
    Łączy listę kafelków (lewa kolumna) z panelem wykresu i statystyk (prawa kolumna).
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("historyView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._setup_stack()
        self._create_widgets()
        self._setup_layout()

    # TODO: Docelowo dane będą pobierane z bazy (np. SQLAlchemy + SQLite).
    def _load_real_data(self):
        """Zwraca rzeczywiste dane z bazy (na razie mock)."""
        return MOCK_DATA

    def _create_widgets(self):
        """Tworzy wszystkie elementy interfejsu."""
        self.title_label = QLabel("HISTORIA TRENINGÓW")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("historyTitle")

        # Lewa kolumna – lista treningów
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.container.setObjectName("historyContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setContentsMargins(0, 15, 15, 0)
        self.container_layout.setSpacing(12)

        # TODO: Zamiast MOCK_DATA – dane z bazy: for record in self._load_real_data():
        for record in MOCK_DATA:
            self.container_layout.addWidget(HistoryCard(record))

        self.scroll_area.setWidget(self.container)

        # Prawa kolumna
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(10, 0, 10, 0)
        right_layout.setSpacing(15)

        self.chart_widget = PerformanceChart(CHART_DATA)
        self.stats_widget = StatsSummary(MOCK_DATA)

        right_layout.addWidget(self.chart_widget, stretch=2)
        right_layout.addWidget(self.stats_widget, stretch=1)

        # Główny układ poziomy
        self.main_content = QWidget()
        main_layout = QVBoxLayout(self.main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        main_layout.addWidget(self.title_label)

        split_layout = QHBoxLayout()
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(20)
        split_layout.addWidget(self.scroll_area, stretch=2)
        split_layout.addWidget(self.right_panel, stretch=1)

        main_layout.addLayout(split_layout)
        self.main_content.setLayout(main_layout)

    def _setup_layout(self):
        """Układa główną zawartość w stosie."""
        self.content_page.setObjectName("historyContentPage")
        layout = QVBoxLayout(self.content_page)
        layout.setContentsMargins(30, 25, 20, 25)
        layout.addWidget(self.main_content)

    def _setup_stack(self):
        """Tworzy stos do przełączania między szkieletem a właściwym widokiem."""
        self.main_stack = QStackedWidget(self)
        self.skeleton_page = SkeletonHistoryView()
        self.content_page = QWidget()
        self.main_stack.addWidget(self.skeleton_page)
        self.main_stack.addWidget(self.content_page)

        m_layout = QVBoxLayout(self)
        m_layout.setContentsMargins(0, 0, 0, 0)
        m_layout.addWidget(self.main_stack)

    def activate_real_ui(self):
        """Przełącza ze szkieletu (skeleton) na właściwy widok z danymi."""
        self.main_stack.setCurrentIndex(ScreenModes.REAL)

    def showEvent(self, event):
        """Po pojawieniu się widoku pokazuje najpierw szkielet, a po chwili właściwe dane."""
        super().showEvent(event)
        self.main_stack.setCurrentIndex(ScreenModes.SKELETON)
        QTimer.singleShot(800, self.activate_real_ui)