from PyQt6.QtWidgets import QComboBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.view().pressed.connect(self.handle_item_pressed)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Sélectionner...")

    def addItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        self.model().appendRow(item)

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        state = item.data(Qt.ItemDataRole.CheckStateRole)
        item.setData(Qt.CheckState.Checked if state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        self.update_display_text()

    def update_display_text(self):
        checked_items = self.checkedItems()
        self.lineEdit().setText(", ".join(checked_items))

    def checkedItems(self):
        return [
            self.model().item(i).text()
            for i in range(self.model().rowCount())
            if self.model().item(i).checkState() == Qt.CheckState.Checked
        ]

    def clear(self):
        self.model().clear()
        self.lineEdit().clear()

    def set_all_checked(self, checked: bool):
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item is not None:
                item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.update_display_text()