from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox, QComboBox
)
from database.gestion_bd import GetCategorie
from .BaseDialog import BaseDialog


class AddEditSousCategorieDialog(BaseDialog):
    def __init__(self, parent=None, sous_categorie=None,categorie = None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier une Sous-Catégorie")

        self.sous_categorie = sous_categorie
        self.categorie = categorie

        # Layout pour la pop-up
        self.layout = QFormLayout()

        # Champs de saisie
        self.nom = QLineEdit(self)
        self.categorie_parent = QComboBox(self)
        categories = GetCategorie()
        for categorie in categories:
            self.categorie_parent.addItem(categorie.nom)
        
        if self.categorie is not None:
            self.categorie_parent.setCurrentText(self.categorie)

        self.layout.addRow(QLabel("Nom:"), self.nom)
        self.layout.addRow(QLabel("Catégorie parent:"), self.categorie_parent)

        # Bouton pour valider
        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

        if self.sous_categorie:
            self.load_sous_categories()

    def load_sous_categories(self):
        self.nom.setText(self.sous_categorie.nom)
        index_type = self.categorie_parent.findText(self.sous_categorie.categorie_parent)
        self.categorie_parent.setCurrentIndex(index_type)

    def submit(self):
        nom = self.nom.text()
        categorie_parent = self.categorie_parent.currentText()

        if not nom or not categorie_parent:
            QMessageBox.warning(self, "Erreur", "Tous les champs doivent être remplis.")
            return

        if self.sous_categorie:
            old_nom = self.sous_categorie.nom
            old_categorie = self.sous_categorie.categorie_parent
            self.sous_categorie.nom = nom
            self.sous_categorie.categorie_parent = categorie_parent
            if self.parent().update_sous_categorie(self.sous_categorie,old_nom,old_categorie):
                self.accept()
            else:
                self.close()
                
        else:
            from models import SousCategorie
            new_sous_categorie = SousCategorie(nom, categorie_parent)
            self.parent().add_sous_categorie(new_sous_categorie)
            self.accept()

        
