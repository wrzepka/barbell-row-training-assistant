# Zawartość pliku: history_view.py
"""
Moduł widoku historii treningów.

Zawiera:
- HistoryCard – rozwijany kafelek pojedynczego treningu,
- PerformanceChart – wykres liniowy postępu wyników,
- StatsSummary – blok statystyk ogólnych,
- HistoryView – główny widget składający lewą listę i prawy panel z formularzem SQLite.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QScrollArea, QFrame, QGroupBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis
from PySide6.QtGui import QPainter, QColor

from app.ui.skeleton_history_view import SkeletonHistoryView
from app.ui.base_view import BaseView
from const import ScreenModes

# Importowanie zaktualizowanych funkcji z warstwy db
from db.database import get_training_statistics, add_training_entry


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
        
        # Zabezpieczenie na wypadek braku danych w bazie
        max_range = len(self.data) - 1 if len(self.data) > 0 else 1
        axis_x.setRange(0, max_range)
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


class HistoryView(QWidget):
    """
    Główny widok historii treningów.
    Łączy dynamiczną listę kafelków z formularzem wprowadzania danych oraz wykresami i statystykami.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("historyView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._setup_stack()
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

        # --- LEWA KOLUMNA: Obszar przewijania kafelków treningowych ---
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

        # --- PRAWA KOLUMNA: Formularz dodawania wpisów + Wykres + Statystyki ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(10, 0, 10, 0)
        self.right_layout.setSpacing(15)

        # Tworzenie widgetu formularza dodawania nowego treningu
        self._create_input_form()

        # Placeholdery pod wykres i statystyki (zostaną uzupełnione w refresh_ui)
        self.chart_widget = QWidget()
        self.stats_widget = QWidget()

        # Budujemy kompletny widok ładując dane po raz pierwszy
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

    def _create_input_form(self):
        """Konstruuje pola formularza służącego do zapisu nowych treningów przez użytkownika."""
        self.form_group = QGroupBox("DODAJ NOWY TRENING")
        self.form_group.setObjectName("historyFormGroup") # Można olować w pliku QSS
        form_layout = QVBoxLayout(self.form_group)
        form_layout.setSpacing(8)

        # Pola liczbowe obok siebie (Ciężar, Powtórzenia, Serie)
        row1_layout = QHBoxLayout()
        
        vbox_w = QVBoxLayout()
        vbox_w.addWidget(QLabel("Ciężar (kg):"))
        self.input_weight = QDoubleSpinBox()
        self.input_weight.setRange(0.0, 300.0)
        self.input_weight.setValue(60.0)
        self.input_weight.setSingleStep(2.5)
        vbox_w.addWidget(self.input_weight)
        
        vbox_r = QVBoxLayout()
        vbox_r.addWidget(QLabel("Powtórzenia:"))
        self.input_reps = QSpinBox()
        self.input_reps.setRange(1, 50)
        self.input_reps.setValue(10)
        vbox_r.addWidget(self.input_reps)

        vbox_s = QVBoxLayout()
        vbox_s.addWidget(QLabel("Serie:"))
        self.input_sets = QSpinBox()
        self.input_sets.setRange(1, 20)
        self.input_sets.setValue(3)
        vbox_s.addWidget(self.input_sets)

        row1_layout.addLayout(vbox_w)
        row1_layout.addLayout(vbox_r)
        row1_layout.addLayout(vbox_s)
        form_layout.addLayout(row1_layout)

        # Czas trwania, ocena procentowa oraz uwagi techniczne
        row2_layout = QHBoxLayout()
        
        vbox_d = QVBoxLayout()
        vbox_d.addWidget(QLabel("Czas (np. 20 min):"))
        self.input_duration = QLineEdit("20 min")
        vbox_d.addWidget(self.input_duration)

        vbox_sc = QVBoxLayout()
        vbox_sc.addWidget(QLabel("Ocena (%) :"))
        self.input_score = QSpinBox()
        self.input_score.setRange(0, 100)
        self.input_score.setValue(90)
        vbox_sc.addWidget(self.input_score)

        row2_layout.addLayout(vbox_d)
        row2_layout.addLayout(vbox_sc)
        form_layout.addLayout(row2_layout)

        form_layout.addWidget(QLabel("Uwagi (rozdzielaj średnikiem ';'):"))
        self.input_to_fix = QLineEdit("Brak uwag")
        form_layout.addWidget(self.input_to_fix)

        self.btn_submit = QPushButton("Dodaj trening do historii")
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.clicked.connect(self._handle_add_training)
        form_layout.addWidget(self.btn_submit)

        self.right_layout.addWidget(self.form_group)

    def _handle_add_training(self):
        """Obsługuje kliknięcie przycisku, wyciąga dane z GUI i zapisuje je w SQLite."""
        weight = self.input_weight.value()
        reps = self.input_reps.value()
        sets = self.input_sets.value()
        duration = self.input_duration.text().strip()
        score = self.input_score.value()
        
        # Pobieramy wpisane uwagi techniczne i dzielimy na listę na podstawie średników
        raw_notes = self.input_to_fix.text().strip()
        to_fix_list = [note.strip() for note in raw_notes.split(";") if note.strip()]
        if not to_fix_list:
            to_fix_list = ["Brak uwag"]

        # Zapis do bazy danych
        add_training_entry(weight, reps, sets, duration, score, to_fix_list)

        # Przywracamy domyślne wartości w formularzu
        self.input_weight.setValue(60.0)
        self.input_reps.setValue(10)
        self.input_sets.setValue(3)
        self.input_duration.setText("20 min")
        self.input_score.setValue(90)
        self.input_to_fix.setText("Brak uwag")

        # Natychmiastowe odświeżenie interfejsu (lista, wykres i statystyki ulegną aktualizacji)
        self.refresh_ui()

    def refresh_ui(self):
        """Czyści stare komponenty interfejsu, odpytuje bazę i rysuje cały widok na nowo."""
        current_data = self._load_real_data()

        # 1. Czyszczenie i ponowne renderowanie kafelków w lewej kolumnie
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for record in current_data:
            self.container_layout.addWidget(HistoryCard(record))

        # 2. Usuwanie starych i dodawanie nowych zaktualizowanych wykresów i podsumowań
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.right_layout.removeWidget(self.chart_widget)
            self.chart_widget.deleteLater()
        
        if hasattr(self, 'stats_widget') and self.stats_widget:
            self.right_layout.removeWidget(self.stats_widget)
            self.stats_widget.deleteLater()

        # Dane do wykresu idą chronologicznie (od najstarszego do najnowszego)
        chart_data_sorted = list(reversed(current_data))
        
        self.chart_widget = PerformanceChart(chart_data_sorted)
        self.stats_widget = StatsSummary(current_data)

        self.right_layout.addWidget(self.chart_widget, stretch=2)
        self.right_layout.addWidget(self.stats_widget, stretch=1)

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
        # Odświeżamy dane z bazy tuż przed wyświetleniem
        self.refresh_ui()
        QTimer.singleShot(800, self.activate_real_ui)