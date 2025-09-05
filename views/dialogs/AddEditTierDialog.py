from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QMessageBox, QComboBox, QCheckBox,QComboBox
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from .BaseDialog import BaseDialog
from database.gestion_bd import *

class AddEditTierDialog(BaseDialog):
    def __init__(self, parent=None, tier=None,type_tier:str=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un Tiers")

        self.tier = tier
        self.type_tier_clicked = type_tier

        # Layout pour la pop-up
        self.layout = QFormLayout()

        # Champs de saisie
        self.nom = QLineEdit(self)
        self.type_tier = QComboBox(self)
        types_tier = GetTypeTier()
        for type in types_tier:
            self.type_tier.addItem(type.nom)

        if self.type_tier_clicked is not None:
            self.type_tier.setCurrentText(self.type_tier_clicked)

        self.cat_def = QComboBox(self)
        self.cat_def.addItem("")
        for categorie in GetCategorie():
            self.cat_def.addItem(categorie.nom)

        self.sous_cat_defaut = QComboBox(self)
        self.update_sous_categories(self.cat_def.currentText())

        self.cat_def.currentIndexChanged.connect(self.on_categorie_changed)

        self.moy_paiement_defaut = QComboBox(self)
        self.moy_paiement_defaut.addItem("")
        for moy_paiement in GetMoyenPaiement():
            self.moy_paiement_defaut.addItem(moy_paiement.nom)

        self.actif = QCheckBox("Actif", self)
        self.actif.setChecked(True)  # Par défaut actif

        self.layout.addRow(QLabel("Nom:"), self.nom)
        self.layout.addRow(QLabel("Type:"), self.type_tier)
        self.layout.addRow(QLabel("Catégorie par défaut:"), self.cat_def)
        self.layout.addRow(QLabel("Sous-Catégorie par défaut:"), self.sous_cat_defaut)
        self.layout.addRow(QLabel("Moyen de paiement par défaut:"), self.moy_paiement_defaut)
        self.layout.addRow(self.actif)

        # Bouton pour valider
        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

        if self.tier:
            self.load_tier()

    def update_sous_categories(self, categorie):
        self.sous_cat_defaut.clear()
        sous_categories = GetSousCategorie(categorie)
        model = QStandardItemModel()        
        item = QStandardItem("")
        item.setToolTip("")
        model.appendRow(item)
        self.sous_cat_defaut.addItem("")
        for sous_categorie in sous_categories:
            item = QStandardItem(sous_categorie.nom)
            item.setToolTip(sous_categorie.nom)
            model.appendRow(item)
            self.sous_cat_defaut.addItem(sous_categorie.nom)

        self.sous_cat_defaut.setModel(model)
            

    def on_categorie_changed(self):
        self.update_sous_categories(self.cat_def.currentText())

    def load_tier(self):
        self.nom.setText(self.tier.nom)
        index_type = self.type_tier.findText(self.tier.type)
        self.type_tier.setCurrentIndex(index_type)

        index_cat = self.cat_def.findText(self.tier.categorie)
        self.cat_def.setCurrentIndex(index_cat)
        self.update_sous_categories(self.tier.categorie)

        index_sous_cat = self.sous_cat_defaut.findText(self.tier.sous_categorie)
        self.sous_cat_defaut.setCurrentIndex(index_sous_cat)

        index_moy = self.moy_paiement_defaut.findText(self.tier.moyen_paiement)
        self.moy_paiement_defaut.setCurrentIndex(index_moy)
        etat = True if self.tier.actif == 'Actif' else False
        self.actif.setChecked(etat)  # Ici on charge la valeur de l'attribut "actif"

    def submit(self):
        nom = self.nom.text()
        type_tier = self.type_tier.currentText()
        cat_def = self.cat_def.currentText()
        sous_cat_defaut = self.sous_cat_defaut.currentText()
        moy_paiement_defaut = self.moy_paiement_defaut.currentText()
        actif = self.actif.isChecked()

        if not nom :
            QMessageBox.warning(self, "Erreur", "Le champs nom doit être remplis.")
            return

        if self.tier:
            self.tier.nom = nom
            self.tier.type = type_tier
            self.tier.categorie = cat_def
            self.tier.sous_categorie = sous_cat_defaut
            self.tier.moyen_paiement = moy_paiement_defaut
            self.tier.actif = actif
            self.parent().update_tier(self.tier)
        else:
            from models import Tier
            new_tier = Tier(nom, type_tier, cat_def, sous_cat_defaut, moy_paiement_defaut, actif=actif)
            self.parent().add_tier(new_tier)

        self.accept()
