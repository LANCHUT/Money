from PyQt6.QtWidgets import (
    QPushButton, QDialog, QVBoxLayout, QComboBox, QHBoxLayout, QLabel
)
from BaseDialog import BaseDialog
class ReplaceMoyenPaiementPopup(BaseDialog):
    def __init__(self, moyen_paiement_disponibles : list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Moyen de paiement lié à des opérations")
        self.setModal(True)
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()

        label = QLabel(
            "Des opérations sont liées au moyen de paiement que vous souhaitez supprimer.\n"
            "Veuillez sélectionner un moyen de paiement de remplacement :", self)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.combo = QComboBox(self)
        self.combo.addItem("",userData={"nom" : ""})
        for moyen_paiement in moyen_paiement_disponibles:
            self.combo.addItem(moyen_paiement.nom, userData={"nom" : moyen_paiement.nom})
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

    def get_selected_moyen_paiement(self):
        return str(self.combo.currentData()["nom"])