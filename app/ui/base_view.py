from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QTimer, Signal
from app.const import ScreenModes
from app.const import SKELETON_MINIMAL_DELAY


class BaseView(QWidget):
    """
    Uniwersalna klasa bazowa dla widoków aplikacji,
    obsługująca mechanizm Skeleton -> Real Content.
    """

    change_page_requested = Signal(int)
    content_ready = Signal()

    def __init__(self, skeleton_widget_class, object_name):
        super().__init__()

        self._minimum_time_elapsed = False
        self._data_loaded = False

        self._setup_view_settings(object_name)
        self._setup_stack(skeleton_widget_class)
        self._setup_transitions()

    def _setup_view_settings(self, object_name):
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _setup_stack(self, skeleton_widget_class):
        self.main_stack = QStackedWidget(self)
        self.skeleton_page = skeleton_widget_class()
        self.content_page = QWidget()

        self.main_stack.addWidget(self.skeleton_page)  # Index 0
        self.main_stack.addWidget(self.content_page)  # Index 1

        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.addWidget(self.main_stack)

    def _setup_transitions(self):
        """Konfiguruje timer do przejścia ze szkieletu do realnego UI."""
        self._transition_timer = QTimer(self)
        self._transition_timer.setSingleShot(True)
        self._transition_timer.setInterval(SKELETON_MINIMAL_DELAY)
        self._transition_timer.timeout.connect(self._on_timer_timeout)

        self.content_ready.connect(self.activate_real_ui)

    def _on_timer_timeout(self):
        """
        Metoda pozwalająca na dłuższe wyświetlanie widoku szkieletowego, gdy zajdzie taka potrzeba
        np: przy długim odczycie danych z bazy danych.
        """
        self._minimum_time_elapsed = True

        if hasattr(self, "_data_loaded") and self._data_loaded:
            self.activate_real_ui()

    def activate_real_ui(self):
        """
        Publiczna metoda do przełączenia widoku ze szkieletu na ten z realną zawartością.
        """
        self.main_stack.setCurrentIndex(ScreenModes.REAL)

    def showEvent(self, event):
        super().showEvent(event)
        self._minimum_time_elapsed = False
        self._data_loaded = False
        self.main_stack.setCurrentIndex(ScreenModes.SKELETON)
        self._transition_timer.start()
