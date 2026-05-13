from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from app.ui.shimmer_block import ShimmerBlock


class SkeletonTrainingView(QWidget):
    """
    Szkielet widoku treningowego z animacją Shimmer.
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # blok dla tekstu
        layout.addWidget(ShimmerBlock(height=80))

        # bloki dla kamer
        cam_layout = QHBoxLayout()
        cam_layout.addWidget(ShimmerBlock())
        cam_layout.addWidget(ShimmerBlock())
        layout.addLayout(cam_layout, stretch=6)

        # blok dla statystyk
        layout.addWidget(ShimmerBlock(height=120))
