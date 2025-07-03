from PyQt6.QtWidgets import (
    QDialog, QLabel, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
)
from PyQt6.QtCore import Qt

class EcheanceDialog(QDialog):
    def __init__(self, comptes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une échéance")
        self.setModal(True)

        self.selected_type = None
        self.selected_compte = None

        # Widgets
        label = QLabel("Quel type d'échéance souhaitez-vous ajouter pour quel compte ?")
        self.combo = QComboBox()
        for compte in comptes:
            self.combo.addItem(compte.nom, userData=str(compte._id))

        btn_operation = QPushButton("Opération")
        btn_position = QPushButton("Position")

        btn_operation.clicked.connect(self.select_operation)
        btn_position.clicked.connect(self.select_position)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.combo)

        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_operation)
        button_layout.addWidget(btn_position)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def select_operation(self):
        self.selected_type = "operation"
        self.selected_compte = self.combo.currentData()
        self.accept()

    def select_position(self):
        self.selected_type = "position"
        self.selected_compte = self.combo.currentData()
        self.accept()