from PyQt6.QtWidgets import QComboBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QModelIndex


class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.view().pressed.connect(self.handle_item_pressed)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Sélectionner...")
        self.addSpecialItem("Tout sélectionner", "select_all")
        self.addSpecialItem("Tout désélectionner", "deselect_all")

    def addItem(self, text):
        """Ajoute un item classique, coché ou non."""
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        self.model().appendRow(item)

    def addSpecialItem(self, text, role_key):
        """Ajoute un item spécial (ex: Tout sélectionner / désélectionner)."""
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setData(role_key, Qt.ItemDataRole.UserRole)
        self.model().appendRow(item)

    def handle_item_pressed(self, index: QModelIndex):
        item = self.model().itemFromIndex(index)
        role_data = item.data(Qt.ItemDataRole.UserRole)

        if role_data == "select_all":
            self.set_all_checked(True)
        elif role_data == "deselect_all":
            self.set_all_checked(False)
        elif item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
            state = item.data(Qt.ItemDataRole.CheckStateRole)
            item.setData(
                Qt.CheckState.Checked if state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked,
                Qt.ItemDataRole.CheckStateRole
            )

        self.update_display_text()

    def checkItemByText(self, text):
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.text() == text and item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)
                break
        self.update_display_text()

    def update_display_text(self):
        checked_items = [
            self.model().item(i).text()
            for i in range(self.model().rowCount())
            if self.model().item(i).checkState() == Qt.CheckState.Checked
            and self.model().item(i).data(Qt.ItemDataRole.UserRole) not in ("select_all", "deselect_all")
        ]
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
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.update_display_text()