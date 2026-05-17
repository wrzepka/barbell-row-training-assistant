from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.ui.shimmer_block import ShimmerBlock

class SkeletonHistoryView(QWidget):
    """
    Szkielet widoku historii z animacją Shimmer.
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # blok dla tekstu
        layout.addWidget(ShimmerBlock(height=40))
        layout.addStretch()