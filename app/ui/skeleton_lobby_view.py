from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from app.ui.shimmer_block import ShimmerBlock

class SkeletonLobbyView(QWidget):
    """
    Szkielet widoku lobby z animacją Shimmer.
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # blok dla tekstu
        layout.addWidget(ShimmerBlock(height=40))
        layout.addStretch()