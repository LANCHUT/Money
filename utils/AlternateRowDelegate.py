from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt


class AlternateRowDelegate(QStyledItemDelegate):
    def __init__(self, even_color, odd_color, parent=None):
        super().__init__(parent)
        self.even_color = QColor(even_color)
        self.odd_color = QColor(odd_color)

    def paint(self, painter, option, index):
        row = index.row()
        bg = self.even_color if (row % 2 == 0) else self.odd_color

        # IMPORTANT : en PyQt6 → StateFlag.State_Selected
        if not (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, QBrush(bg))

        super().paint(painter, option, index)
