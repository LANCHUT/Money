from PyQt6.QtWidgets import (
    QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QLabel
)
from BaseDialog import BaseDialog
class ReplaceSousCategoriePopup(BaseDialog):
    def __init__(self, sous_categories_disponibles, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sous-catégorie liée à des opérations")
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()

        label = QLabel(
            "Des opérations sont liées à la sous-categorie que vous souhaitez supprimer.\n"
            "Veuillez sélectionner une sous-catégorie de remplacement :", self)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.combo = QComboBox(self)
        for sous_categorie in sous_categories_disponibles:
            self.combo.addItem(sous_categorie.nom, userData={"nom" : sous_categorie.nom, "categorie_parent" : sous_categorie.categorie_parent})
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

    def get_selected_sous_categorie(self):
        return str(self.combo.currentData()["nom"])