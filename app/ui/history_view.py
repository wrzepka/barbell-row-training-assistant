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
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis
from PySide6.QtGui import QPainter, QColor

from app.ui.skeleton_history_view import SkeletonHistoryView
from app.ui.base_view import BaseView

# POŁĄCZENIE Z BAZĄ DANYCH
from app.db.database import get_training_statistics


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

        stats_lbl = QLabel(f"{data['sets']} serie | {data['reps']} powt. łącznie | {data['duration']}")
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
        det_layout.setSpacing(6)

        line = QFrame()
        line.setObjectName("separator")
        det_layout.addWidget(line)

        # ── Serie ──────────────────────────────────────────────────────────────
        sets_detail = data.get("sets_detail", [])
        if sets_detail:
            sets_title = QLabel("SERIE:")
            sets_title.setObjectName("fixTitle")
            det_layout.addWidget(sets_title)

            for s in sets_detail:
                row = QLabel(
                    f"  Seria {s['set_nr']}:  {s['weight']:.1f} kg  ×  {s['reps']} powt."
                )
                row.setObjectName("bulletLabel")
                det_layout.addWidget(row)

            # Separator przed uwagami
            sep2 = QFrame()
            sep2.setObjectName("separator")
            det_layout.addWidget(sep2)

        # ── Uwagi z analizy ────────────────────────────────────────────────────
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


class PerformanceChart(QFrame):
    """Widget z wykresem liniowym postępu wyników w czasie."""

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setObjectName("performanceChartFrame")
        # STYLIZE USUNIĘTE STĄD – PRZENIESIONE DO STYLE.QSS
        self._setup_chart()

    def _setup_chart(self):
        series = QLineSeries()
        series.setName("Postęp wyników (%)")

        for i, record in enumerate(self.data):
            series.append(i, record["score"])

        chart = QChart()
        chart.addSeries(series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)
        chart.legend().setLabelColor(QColor("white"))

        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(QColor("#2a2a2a"))
        chart.setPlotAreaBackgroundBrush(QColor("#2a2a2a"))
        chart.setPlotAreaBackgroundVisible(True)
        chart.layout().setContentsMargins(0, 0, 0, 0)

        # Oś X
        axis_x = QCategoryAxis()
        axis_x.setLabelsColor(QColor("#aaaaaa"))
        axis_x.setTitleText("Trening (od najstarszego)")
        axis_x.setTitleBrush(QColor("white"))
        axis_x.setGridLineColor(QColor("#555555"))

        seen_labels = set()
        for i, record in enumerate(self.data):
            label = record["date"][5:10]  # MM-DD
            while label in seen_labels:
                label += " "
            seen_labels.add(label)
            axis_x.append(label, i)

        max_range = len(self.data) - 1 if len(self.data) > 0 else 1
        axis_x.setRange(0, max_range)

        try:
            axis_x.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
        except AttributeError:
            pass

        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # Oś Y
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTickCount(5)
        axis_y.setTitleText("Wynik (%)")
        axis_y.setTitleBrush(QColor("white"))
        axis_y.setLabelsColor(QColor("#aaaaaa"))
        axis_y.setLabelFormat("%d")
        axis_y.setGridLineColor(QColor("#555555"))
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        pen = series.pen()
        pen.setColor(QColor("#adff2f"))
        pen.setWidth(2)
        series.setPen(pen)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)

        # Wysokość wykresu dostosowana do dużego widoku
        chart_view.setMinimumHeight(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(chart_view)


class StatsSummary(QWidget):
    """Dolny blok statystyk ogólnych."""

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setObjectName("statsSummary")
        self._setup_ui()

    def _setup_ui(self):
        total_trainings = len(self.data)

        if total_trainings > 0:
            avg_score = sum(d["score"] for d in self.data) / total_trainings
            best_score = max(d["score"] for d in self.data)
            worst_score = min(d["score"] for d in self.data)
            all_notes = [note for d in self.data for note in d["to_fix"] if note != "Brak uwag"]
            most_common_note = max(set(all_notes), key=all_notes.count) if all_notes else "Brak krytycznych uwag"
        else:
            avg_score = best_score = worst_score = 0
            most_common_note = "Brak danych"

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


class HistoryView(BaseView):
    """
    Główny widok historii treningów.
    Łączy dynamiczną lista kafelków z wykresami i statystykami.
    """

    def __init__(self):
        super().__init__(SkeletonHistoryView, "historyView")

        self._create_widgets()
        self._setup_layout()

    def _load_real_data(self):
        """Zwraca rzeczywiste dane z bazy SQLite."""
        return get_training_statistics()

    def _create_widgets(self):
        """Tworzy wszystkie elementy interfejsu."""
        self.title_label = QLabel("HISTORIA TRENINGÓW")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("historyTitle")

        # --- LEWA KOLUMNA ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.container.setObjectName("historyContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setContentsMargins(0, 15, 15, 0)
        self.container_layout.setSpacing(12)

        self.scroll_area.setWidget(self.container)

        # --- PRAWA KOLUMNA ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(10, 0, 10, 0)
        self.right_layout.setSpacing(25)

        self.chart_widget = None
        self.stats_widget = None

        self.refresh_ui()

        # --- GŁÓWNY UKŁAD STRONY ---
        self.main_content = QWidget()
        main_layout = QVBoxLayout(self.main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)
        main_layout.addWidget(self.title_label)

        self.split_layout = QHBoxLayout()
        self.split_layout.setContentsMargins(0, 0, 0, 0)
        self.split_layout.setSpacing(20)
        self.split_layout.addWidget(self.scroll_area, stretch=2)
        self.split_layout.addWidget(self.right_panel, stretch=1)

        main_layout.addLayout(self.split_layout)
        self.main_content.setLayout(main_layout)

    def refresh_ui(self):
        """Czyści stare komponenty interfejsu, odpytuje bazę i rysuje cały widok na nowo."""
        current_data = self._load_real_data()

        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for record in current_data:
            self.container_layout.addWidget(HistoryCard(record))

        if self.chart_widget is not None:
            self.right_layout.removeWidget(self.chart_widget)
            self.chart_widget.deleteLater()
            self.chart_widget = None

        if self.stats_widget is not None:
            self.right_layout.removeWidget(self.stats_widget)
            self.stats_widget.deleteLater()
            self.stats_widget = None

        chart_data_sorted = list(reversed(current_data))

        self.chart_widget = PerformanceChart(chart_data_sorted)
        self.stats_widget = StatsSummary(current_data)

        self.right_layout.addWidget(self.chart_widget, stretch=1)
        self.right_layout.addWidget(self.stats_widget, stretch=0)
        self.right_layout.addStretch()

    def _setup_layout(self):
        """Układa główną zawartość w stosie."""
        self.content_page.setObjectName("historyContentPage")
        layout = QVBoxLayout(self.content_page)
        layout.setContentsMargins(30, 25, 20, 25)
        layout.addWidget(self.main_content)

    def showEvent(self, event):
        """Odświeża dane za każdym razem gdy użytkownik przełączy się na tę zakładkę."""
        super().showEvent(event)
        self.refresh_ui()