from PyQt6.QtWidgets import (
    QDialog, QLabel, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
)
from PyQt6.QtCore import Qt

class ImportDialog(QDialog):
    def __init__(self, comptes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer un fichier qif")
        self.setModal(True)

        self.selected_type = None
        self.selected_compte = None

        # Widgets
        label = QLabel("Sur quel compte voulez-vous importer les données ?")
        self.combo = QComboBox()
        for compte in comptes:
            self.combo.addItem(compte.nom, userData=str(compte._id))

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self.combo)

        # Buttons
        button_layout = QHBoxLayout()
        
        # Add the 'Valider' button
        self.validate_button = QPushButton("Valider")
        # Connect the 'clicked' signal to the accept() slot of the QDialog
        self.validate_button.clicked.connect(self.accept) 
        button_layout.addWidget(self.validate_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        
    def get_selected_compte_id(self):
        """
        Returns the ID of the selected account if the dialog was accepted.
        """
        if self.result() == QDialog.DialogCode.Accepted:
            return self.combo.currentData()
        return None