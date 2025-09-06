from PyQt6.QtWidgets import (
    QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QLabel
)
from views.dialogs.BaseDialog import BaseDialog

class ReplaceTierPopup(BaseDialog):
    def __init__(self, tiers_disponibles, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tiers lié à des opérations")
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()

        label = QLabel(
            "Des opérations sont liées au tiers que vous souhaitez supprimer.\n"
            "Veuillez sélectionner un tiers de remplacement :", self)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.combo = QComboBox(self)
        for tier in tiers_disponibles:
            self.combo.addItem(tier.nom, userData=tier._id)
        layout.addWidget(self.combo)

        button_layout = QHBoxLayout()
        valider_btn = QPushButton("Valider")
        annuler_btn = QPushButton("Annuler")
        valider_btn.clicked.connect(self.accept)
        annuler_btn.clicked.connect(self.reject)

        button_layout.addWidget(valider_btn)
        button_layout.addWidget(annuler_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_selected_tier_id(self):
        return str(self.combo.currentData())