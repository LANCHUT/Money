from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QComboBox
)
from Datas import Compte, TypeCompte
from BaseDialog import BaseDialog


class AddEditAccountDialog(BaseDialog):
    def __init__(self, parent=None, compte: Compte = None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un Compte")

        self.compte = compte

        # Layout principal
        self.layout = QFormLayout()

        # Champs
        self.nom_input = QLineEdit(self)
        self.solde_input = QLineEdit(self)
        self.solde_input.textEdited.connect(self.format_solde_input)
        self.type_input = QComboBox(self)
        self.banque_input = QLineEdit(self)

        # Remplissage de la liste des types
        for type_compte in TypeCompte.return_list():
            self.type_input.addItem(type_compte)

        # Si modification, pré-remplir
        if self.compte:
            self.nom_input.setText(self.compte.nom)
            self.banque_input.setText(self.compte.nom_banque)
            index = self.type_input.findText(self.compte.type)
            if index != -1:
                self.type_input.setCurrentIndex(index)
                self.type_input.setDisabled(True)  # Empêche la modification du type

            try:
                solde_float = float(self.compte.solde)
            except ValueError:
                solde_float = 0.0

            self.solde_input.setText(f"{solde_float:,.2f}".replace(",", " ").replace(".", ","))
            self.solde_input.setDisabled(True)

        # Ajout des champs
        self.layout.addRow(QLabel("Nom du Compte:"), self.nom_input)
        self.layout.addRow(QLabel("Solde :"), self.solde_input)
        self.layout.addRow(QLabel("Type de Compte:"), self.type_input)
        self.layout.addRow(QLabel("Nom de la Banque:"), self.banque_input)

        # Bouton de validation
        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

    def submit(self):
        nom = self.nom_input.text()
        solde_str = self.solde_input.text().replace(" ", "").replace(",", ".")
        type_compte = self.type_input.currentText()
        banque = self.banque_input.text()

        if not nom or not type_compte or not banque or (not solde_str and not self.compte):
            QMessageBox.warning(self, "Erreur", "Tous les champs doivent être remplis.")
            return

        if self.compte:
            # Mise à jour
            self.compte.nom = nom
            self.compte.type = type_compte
            self.compte.nom_banque = banque
            self.parent().update_account(self.compte)
        else:
            try:
                solde = float(solde_str)
            except ValueError:
                QMessageBox.warning(self, "Erreur", "Le solde doit être un nombre valide.")
                return

            nouveau_compte = Compte(nom, solde, type_compte, banque)
            self.parent().add_compte(nouveau_compte)

        self.accept()

    def format_solde_input(self):
        text = self.solde_input.text()
        clean_text = ''.join(c for c in text if c.isdigit() or c in [',', '.'])
        clean_text = clean_text.replace(",", ".")

        if '.' in clean_text:
            partie_entiere, partie_decimale = clean_text.split('.', 1)
            partie_entiere = "{:,}".format(int(partie_entiere)).replace(",", " ")
            formatted = partie_entiere + ',' + partie_decimale
        else:
            if clean_text:
                formatted = "{:,}".format(int(clean_text)).replace(",", " ")
            else:
                formatted = ""

        self.solde_input.blockSignals(True)
        self.solde_input.setText(formatted)
        self.solde_input.blockSignals(False)
        self.solde_input.setCursorPosition(len(formatted))
