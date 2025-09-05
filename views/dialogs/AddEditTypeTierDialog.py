from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox
)
from models import TypeTier
from .BaseDialog import BaseDialog


class AddEditTypeTierDialog(BaseDialog):
    def __init__(self, parent=None, type_tier:TypeTier=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un type de tier")

        self.type_tier = type_tier

        # Layout pour la pop-up
        self.layout = QFormLayout()

        # Champs de saisie
        self.nom = QLineEdit(self)
        if self.type_tier:
            self.nom.setText(self.type_tier.nom)

        self.layout.addRow(QLabel("Nom:"), self.nom)

        # Bouton pour valider
        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

    def submit(self):
        nom = self.nom.text()

        if not nom:
            QMessageBox.warning(self, "Erreur", "Tous les champs doivent être remplis.")
            return

        if self.type_tier:
            old_nom = self.type_tier.nom
            self.type_tier.nom = nom
            self.parent().update_type_tier(self.type_tier,old_nom)
        else:
            new_type_tier = TypeTier(nom)
            self.parent().add_type_tier(new_type_tier)

        self.accept()
