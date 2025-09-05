from PyQt6.QtWidgets import (
    QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QLabel
)
from .BaseDialog import BaseDialog
class ReplaceCategoriePopup(BaseDialog):
    def __init__(self, categories_disponibles : list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Catégorie liée à des opérations")
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()

        label = QLabel(
            "Des opérations sont liées à la categorie que vous souhaitez supprimer.\n"
            "Veuillez sélectionner une catégorie de remplacement :", self)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.combo = QComboBox(self)
        self.combo.addItem("",userData={"nom" : ""})
        for categorie in categories_disponibles:
            self.combo.addItem(categorie.nom, userData={"nom" : categorie.nom})
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

    def get_selected_categorie(self):
        return str(self.combo.currentData()["nom"])