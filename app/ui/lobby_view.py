from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PySide6.QtGui import QColor, QPainter, QFont

from app.core.config import EXAMPLE_VIDEO
from app.ui.base_view import BaseView
from app.ui.skeleton_lobby_view import SkeletonLobbyView


class LobbyView(BaseView):
    """
    Widok lobby (strona główna) aplikacji treningowej.
    Wyświetla informacje o systemie, opis ćwiczenia, motywację,
    tygodniowy wykres aktywności oraz podsumowanie ostatniego treningu.
    Umożliwia przejście do szczegółów treningu.
    """

    def __init__(self):
        """
        Inicjalizuje widok lobby.
        Ładuje szkielet UI (SkeletonLobbyView) i tworzy wszystkie elementy interfejsu.
        """
        super().__init__(SkeletonLobbyView, "lobbyView")
        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """
        Tworzy wszystkie widgety składowe widoku lobby:
        - tytuł strony
        - lewy panel z opisem ćwiczenia i stanem systemu
        - prawy panel z wykresem tygodniowym i ostatnią sesją
        """
        # Tytuł strony
        self.title_label = QLabel("BARBEL ROW TRENING")
        self.title_label.setObjectName("lobbyTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        # LEWY PANEL – bez stretchów, wyrównany do góry
        self.left_panel = QWidget()
        self.left_panel.setObjectName("lobbyLeftPanel")
        self.left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(20, 20, 20, 0)
        left_layout.setSpacing(10)
        left_layout.setAlignment(Qt.AlignTop)   # przyklejenie zawartości do góry

        # Etykieta statusu systemu
        self.system_status = QLabel("SYSTEM GOTOWY")
        self.system_status.setObjectName("systemStatus")
        left_layout.addWidget(self.system_status)

        # Krótki opis ćwiczenia
        self.ready_label = QLabel("Krótki opis ćwiczenia")
        self.ready_label.setObjectName("readyLabel")
        left_layout.addWidget(self.ready_label)

        # Długi opis techniki wykonania wiosłowania sztangą
        self.program_desc = QLabel(
            "Wiosłowanie sztangą to ćwiczenie na plecy (głównie najszerszy grzbietu i środek pleców).\n"
            "Jak robić:\n"
            "\t1. Łapiesz sztangę, pochylasz prosty tułów w przód (kolana lekko ugięte).\n"
            "\t2.Przyciągasz sztangę do brzucha, prowadząc\nłokcie blisko ciała i mocno ściągając łopatki.\n"
            "\t3.Kontrolowanie opuszczasz.\n"
            "Ważne: Plecy muszą być przez cały czas idealnie proste – zero kociego grzbietu."
        )
        self.program_desc.setObjectName("programDesc")
        self.program_desc.setWordWrap(True)
        left_layout.addWidget(self.program_desc)

        self._setup_example_video_player(left_layout, EXAMPLE_VIDEO)

        # Etykieta motywacyjna
        self.motivation = QLabel("🔥 Gotowy na dzisiejszy trening?")
        self.motivation.setObjectName("motivationLabel")
        left_layout.addWidget(self.motivation)

        # PRAWY PANEL – rozciąganie w pionie
        self.right_panel = QWidget()
        self.right_panel.setObjectName("lobbyRightPanel")
        self.right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(20, 0, 20, 0)
        right_layout.setSpacing(15)
        right_layout.setAlignment(Qt.AlignTop)

        # Widget tygodniowy (wykres słupkowy)
        self.weekly_widget = QWidget()
        self.weekly_widget.setObjectName("weeklyWidget")
        weekly_layout = QVBoxLayout(self.weekly_widget)
        weekly_layout.setContentsMargins(15, 15, 15, 15)
        weekly_layout.setSpacing(5)

        weekly_header = QLabel("TYGODNIOWY WYNIK")
        weekly_header.setObjectName("weeklyHeader")
        weekly_percent = QLabel("+12% vs Ostatni tydzień")
        weekly_percent.setObjectName("weeklyPercent")

        self.chart_view = self._create_weekly_chart()
        weekly_layout.addWidget(weekly_header)
        weekly_layout.addWidget(weekly_percent)
        weekly_layout.addWidget(self.chart_view)
        right_layout.addWidget(self.weekly_widget)

        # Widget ostatniej sesji treningowej
        self.last_session_widget = QWidget()
        self.last_session_widget.setObjectName("lastSessionWidget")
        session_layout = QVBoxLayout(self.last_session_widget)
        session_layout.setContentsMargins(15, 15, 15, 15)
        session_layout.setSpacing(8)

        session_title = QLabel("OSTATNI TRENING")
        session_title.setObjectName("sessionTitle")
        session_name = QLabel("Hipertrofia")
        session_name.setObjectName("sessionName")
        session_detail = QLabel("Nogi & Core • 2 dni temu")
        session_detail.setObjectName("sessionDetail")

        # Poziomy układ dla statystyk (czas, objętość)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        duration_box = self._create_stat_box("CZAS", "1h 15m")
        volume_box = self._create_stat_box("OBJĘTOŚĆ", "12.5k")
        stats_layout.addWidget(duration_box)
        stats_layout.addWidget(volume_box)

        # Przycisk do przejścia do szczegółów treningu
        view_details_btn = QPushButton("ZOBACZ SZCZEGÓŁY")
        view_details_btn.setObjectName("viewDetailsButton")
        view_details_btn.setCursor(Qt.PointingHandCursor)
        view_details_btn.clicked.connect(self._on_view_details)

        session_layout.addWidget(session_title)
        session_layout.addWidget(session_name)
        session_layout.addWidget(session_detail)
        session_layout.addLayout(stats_layout)
        session_layout.addWidget(view_details_btn)

        right_layout.addWidget(self.last_session_widget)

        # Główny układ poziomych kolumn (lewy panel + prawy panel)
        self.main_content = QWidget()
        main_layout = QHBoxLayout(self.main_content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        main_layout.addWidget(self.left_panel, stretch=2)
        main_layout.addWidget(self.right_panel, stretch=3)

    def _create_weekly_chart(self) -> QChartView:
        """
        Tworzy i konfiguruje wykres słupkowy przedstawiający tygodniową aktywność (minuty).
        Wykres zawiera dane dla każdego dnia tygodnia, z dostosowanym stylem wizualnym.

        Returns:
            QChartView: Widok wykresu gotowy do wstawienia do layoutu.
        """
        days = ["PON", "WT", "ŚR", "CZW", "PT", "SOB", "NIE"]
        values = [110, 82, 55, 60, 75, 30, 40]

        # Zestaw danych dla słupków
        bar_set = QBarSet("Aktywność (min)")
        for v in values:
            bar_set.append(v)
        bar_set.setColor(QColor("#CCFF00"))

        # Seria słupkowa
        series = QBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.7)
        series.setLabelsVisible(True)
        try:
            series.setLabelsFont(QFont("Arial", 9, QFont.Bold))
            series.setLabelsColor(QColor("#FFFFFF"))
        except Exception:
            pass

        # Główny obiekt wykresu
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundBrush(Qt.transparent)
        chart.setPlotAreaBackgroundBrush(QColor("#1e1e1e"))
        chart.setPlotAreaBackgroundVisible(True)
        chart.setMinimumHeight(200)

        # Oś X (kategorie dni)
        axis_x = QBarCategoryAxis()
        axis_x.append(days)
        axis_x.setLabelsColor(QColor("#FFFFFF"))
        axis_x.setLabelsFont(QFont("Arial", 9, QFont.Bold))
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # Oś Y (wartości w minutach)
        axis_y = QValueAxis()
        axis_y.setRange(0, max(values) + 20)
        axis_y.setTitleText("min")
        axis_y.setTitleBrush(QColor("#FFFFFF"))
        axis_y.setTitleFont(QFont("Arial", 9, QFont.Bold))
        axis_y.setLabelsColor(QColor("#FFFFFF"))
        axis_y.setLabelsFont(QFont("Arial", 8))
        axis_y.setLabelFormat("%d")
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.setBackgroundVisible(True)
        chart.setDropShadowEnabled(False)

        # Widok wykresu z włączonym antyaliasingiem
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(200)
        return chart_view

    def _create_stat_box(self, title, value):
        """
        Tworzy pojedynczy widget kafelka statystyki (np. CZAS, OBJĘTOŚĆ).
        Zawiera tytuł i wartość.

        Args:
            title (str): Tytuł statystyki (np. "CZAS").
            value (str): Wartość statystyki (np. "1h 15m").

        Returns:
            QWidget: Widget kafelka statystyki.
        """
        box = QWidget()
        box.setObjectName("statBox")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(8, 8, 8, 8)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("statTitle")
        value_lbl = QLabel(value)
        value_lbl.setObjectName("statValue")

        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        return box

    def _setup_layout(self):
        """
        Układa wszystkie elementy na stronie content_page:
        - tytuł na górze
        - główny kontener z dwoma panelami pod spodem
        Ustawia marginesy i odstępy.
        """
        self.content_page.setObjectName("lobbyContentPage")
        layout = QVBoxLayout(self.content_page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        layout.addWidget(self.title_label)
        layout.addWidget(self.main_content)

    def _on_view_details(self):
        """
        Slot wywoływany po kliknięciu przycisku "ZOBACZ SZCZEGÓŁY".
        Przełącza stronę na widok szczegółów treningu (indeks 2).
        """
        main_window = self.window()
        if hasattr(main_window, 'switch_page'):
            main_window.switch_page(2)

    def _setup_example_video_player(self, layout, video_path):
        """
        Tworzy i konfiguruje nieskończony odtwarzacz video.
        """
        self.video_widget = QVideoWidget()
        self.video_widget.setObjectName("videoWidget")
        self.video_widget.setMinimumHeight(150)
        layout.addWidget(self.video_widget)

        # Inicjalizacja odtwarzacza
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.media_player.play()