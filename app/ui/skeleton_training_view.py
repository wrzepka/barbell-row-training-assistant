from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from app.ui.shimmer_block import ShimmerBlock


class SkeletonTrainingView(QWidget):
    """
    Szkielet widoku treningowego z animacją Shimmer.
    """

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        # bloki dla kamer
        cam_layout = QVBoxLayout()
        cam_layout.setSpacing(15)
        cam_layout.addWidget(ShimmerBlock())
        cam_layout.addWidget(ShimmerBlock())
        layout.addLayout(cam_layout, stretch=6)

        # blok dla statystyk
        panel_layout = QVBoxLayout()
        panel_layout.setSpacing(15)
        panel_layout.addWidget(ShimmerBlock(), stretch=4)
        panel_layout.addWidget(ShimmerBlock(), stretch=6)
        layout.addLayout(panel_layout, stretch=4)
