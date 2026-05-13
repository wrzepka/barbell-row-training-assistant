from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, QVariantAnimation
from PySide6.QtGui import QPainter, QLinearGradient, QColor


class ShimmerBlock(QFrame):
    """
    Widget typu Skeleton z efektem animowanego gradientu (shimmer).
    """

    def __init__(self, height=None, width=None):
        super().__init__()

        if height: self.setFixedHeight(height)
        if width: self.setFixedWidth(width)

        # kolory bazowe
        self._base_color = QColor("#252525")
        self._highlight_color = QColor("#333333")

        # zmienna sterująca pozycją gradientu (od -1.0 do 2.0)
        self._gradient_pos = -1.0

        # konfiguracja animacji
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(1500)  # czas trwania jednego przejścia (ms)
        self.animation.setStartValue(-1.0)
        self.animation.setEndValue(2.0)
        self.animation.setLoopCount(-1)  # zapętlenie w nieskończoność
        self.animation.valueChanged.connect(self._update_gradient)
        self.animation.start()

    def _update_gradient(self, value):
        """
        Slot aktualizujący pozycję i wymuszający przerysowanie.
        """
        self._gradient_pos = value
        self.update()

    def paintEvent(self, event):
        """
        Ręczne rysowanie animowanego gradientu.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Tworzenie gradientu liniowego
        gradient = QLinearGradient(
            self.width() * self._gradient_pos, 0,
            self.width() * (self._gradient_pos + 0.5), 0
        )

        gradient.setColorAt(0, self._base_color)
        gradient.setColorAt(0.5, self._highlight_color)
        gradient.setColorAt(1, self._base_color)

        # Rysowanie tła z zaokrąglonymi rogami
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
