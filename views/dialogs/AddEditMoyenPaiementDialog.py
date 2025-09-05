from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QMessageBox, QComboBox, QCheckBox
)
from models import MoyenPaiement
from .BaseDialog import BaseDialog

class AddEditMoyenPaiementDialog(BaseDialog):
    def __init__(self, parent=None, moyen_paiement:MoyenPaiement=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un moyen de paiement")
        self.moyen_paiement = moyen_paiement

        # Layout pour la pop-up
        self.layout = QFormLayout()

        # Champs de saisie
        self.nom = QLineEdit(self)
        if self.moyen_paiement:
            self.nom.setText(self.moyen_paiement.nom)

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

        if self.moyen_paiement:
            old_nom = self.moyen_paiement.nom
            self.moyen_paiement.nom = nom
            self.parent().update_moyen_paiement(self.moyen_paiement,old_nom)
        else:
            new_moyen_paiement = MoyenPaiement(nom)
            self.parent().add_moyen_paiement(new_moyen_paiement)

        self.accept()
