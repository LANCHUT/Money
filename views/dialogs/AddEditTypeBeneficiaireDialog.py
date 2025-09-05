from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QMessageBox, QComboBox, QCheckBox
)
from models import TypeBeneficiaire
from .BaseDialog import BaseDialog


class AddEditTypeBeneficiaireDialog(BaseDialog):
    def __init__(self, parent=None, type_beneficiaire:TypeBeneficiaire=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un type de bénéficiaire")

        self.type_beneficiaire = type_beneficiaire

        # Layout pour la pop-up
        self.layout = QFormLayout()

        # Champs de saisie
        self.nom = QLineEdit(self)
        if self.type_beneficiaire:
            self.nom.setText(self.type_beneficiaire.nom)

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

        if self.type_beneficiaire:
            old_nom = self.type_beneficiaire.nom
            self.type_beneficiaire.nom = nom
            self.parent().update_type_beneficiaire(self.type_beneficiaire,old_nom)
        else:
            new_type_beneficiaire = TypeBeneficiaire(nom)
            self.parent().add_type_beneficiaire(new_type_beneficiaire)

        self.accept()
