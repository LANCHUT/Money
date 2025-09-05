from PyQt6.QtWidgets import (
    QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QLabel
)
from .BaseDialog import BaseDialog

class ReplaceTypeTierPopup(BaseDialog):
    def __init__(self, type_tier_disponibles : list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Catégorie liée à des opérations")
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()

        label = QLabel(
            "Des opérations sont liées au type de tiers que vous souhaitez supprimer.\n"
            "Veuillez sélectionner un type de tiers de remplacement :", self)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.combo = QComboBox(self)
        self.combo.addItem("",userData={"nom" : ""})
        for type_tier in type_tier_disponibles:
            self.combo.addItem(type_tier.nom, userData={"nom" : type_tier.nom})
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

    def get_selected_type_tier(self):
        return str(self.combo.currentData()["nom"])