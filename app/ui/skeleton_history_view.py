from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from app.ui.shimmer_block import ShimmerBlock

class SkeletonHistoryView(QWidget):
    """
    Szkielet widoku historii z animacją Shimmer.
    """

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(30)

        main_layout.addWidget(ShimmerBlock(height=40, width=300), alignment=Qt.AlignmentFlag.AlignCenter)

        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(50)

        # zawartość lewej kolumny
        left_column = ShimmerBlock()
        columns_layout.addWidget(left_column, stretch=7)

        right_column_layout = QVBoxLayout()
        right_column_layout.setSpacing(20)

        # zawartość prawej kolumny
        training_graph_card = ShimmerBlock()
        right_column_layout.addWidget(training_graph_card, stretch=5)
        summary_card = ShimmerBlock()
        right_column_layout.addWidget(summary_card, stretch=2)

        columns_layout.addLayout(right_column_layout, stretch=3)
        main_layout.addLayout(columns_layout)