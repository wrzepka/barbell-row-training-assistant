from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QTimer
from app.const import ScreenModes


class BaseView(QWidget):
    """
    Uniwersalna klasa bazowa dla widoków aplikacji,
    obsługująca mechanizm Skeleton -> Real Content.
    """

    def __init__(self, skeleton_widget_class, object_name):
        super().__init__()

        self._setup_view_settings(object_name)
        self._setup_stack(skeleton_widget_class)

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

    def activate_real_ui(self):
        """
        Publiczna metoda do przełączenia widoku ze szkieletu na ten z realną zawartością.
        """
        self.main_stack.setCurrentIndex(ScreenModes.REAL)

    def showEvent(self, event):
        """Wspólna logika pokazywania widoku."""
        super().showEvent(event)
        self.main_stack.setCurrentIndex(ScreenModes.SKELETON)

        # Symulacja opóźnienia ładowania
        QTimer.singleShot(1500, self.activate_real_ui)
