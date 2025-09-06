from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QMessageBox, QComboBox, QCheckBox
)
from models import Categorie
from views.dialogs.BaseDialog import BaseDialog


class AddEditCategorieDialog(BaseDialog):
    def __init__(self, parent=None, categorie:Categorie=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier une Catégorie")

        self.categorie = categorie

        # Layout pour la pop-up
        self.layout = QFormLayout()

        # Champs de saisie
        self.nom = QLineEdit(self)
        if self.categorie:
            self.nom.setText(self.categorie.nom)

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

        if self.categorie:
            old_nom = self.categorie.nom
            self.categorie.nom = nom
            self.parent().update_categorie(self.categorie,old_nom)
        else:
            new_categorie = Categorie(nom)
            self.parent().add_categorie(new_categorie)

        self.accept()
