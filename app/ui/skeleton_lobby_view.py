from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from app.ui.shimmer_block import ShimmerBlock

class SkeletonLobbyView(QWidget):
    """
    Szkielet widoku lobby z animacją Shimmer.
    """

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 75, 50)
        main_layout.setSpacing(30)

        main_layout.addWidget(ShimmerBlock(height=40, width=300), alignment=Qt.AlignmentFlag.AlignCenter)

        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(40)

        # zawartość prawej kolumny
        left_column = ShimmerBlock()
        columns_layout.addWidget(left_column, stretch=4)

        right_column_layout = QVBoxLayout()
        right_column_layout.setSpacing(20)

        # zawartość prawej kolumny
        weekly_result_card = ShimmerBlock()
        right_column_layout.addWidget(weekly_result_card, stretch=6)
        last_training_card = ShimmerBlock()
        right_column_layout.addWidget(last_training_card, stretch=4)

        columns_layout.addLayout(right_column_layout, stretch=6)
        main_layout.addLayout(columns_layout)