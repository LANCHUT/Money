from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox, QComboBox
)
from GestionBD import GetTypeBeneficiaire
from BaseDialog import BaseDialog
from Datas import Beneficiaire


class AddEditBeneficiaireDialog(BaseDialog):
    def __init__(self, parent=None, beneficiaire:Beneficiaire=None,type_beneficiaire:str=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un bénéficiaire")

        self.beneficiaire = beneficiaire
        self.type_beneficiaire = type_beneficiaire

        # Layout pour la pop-up
        self.layout = QFormLayout()

        # Champs de saisie
        self.nom = QLineEdit(self)
        self.type_beneficiaire_parent = QComboBox(self)
        type_beneficiaires = GetTypeBeneficiaire()
        for type_beneficiaire in type_beneficiaires:
            self.type_beneficiaire_parent.addItem(type_beneficiaire.nom)

        if self.type_beneficiaire is not None:
            self.type_beneficiaire_parent.setCurrentText(self.type_beneficiaire)

        self.layout.addRow(QLabel("Nom:"), self.nom)
        self.layout.addRow(QLabel("Type bénéficiaire:"), self.type_beneficiaire_parent)

        # Bouton pour valider
        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

        if self.beneficiaire:
            self.load_beneficiaire()

    def load_beneficiaire(self):
        self.nom.setText(self.beneficiaire.nom)
        index_type = self.type_beneficiaire_parent.findText(self.beneficiaire.type_beneficiaire)
        self.type_beneficiaire_parent.setCurrentIndex(index_type)

    def submit(self):
        nom = self.nom.text()
        type_beneficiaire = self.type_beneficiaire_parent.currentText()

        if not nom or not type_beneficiaire:
            QMessageBox.warning(self, "Erreur", "Tous les champs doivent être remplis.")
            return

        if self.beneficiaire:
            old_nom = self.beneficiaire.nom
            old_type_beneficiaire = self.beneficiaire.type_beneficiaire
            self.beneficiaire.nom = nom
            self.beneficiaire.type_beneficiaire = type_beneficiaire
            if self.parent().update_beneficiaire(self.beneficiaire,old_nom,old_type_beneficiaire):
                self.accept()
            else:
                self.close()
        else:
            new_beneficiaire = Beneficiaire(nom, type_beneficiaire)
            self.parent().add_beneficiaire(new_beneficiaire)

        self.accept()
