from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QEvent, QDate
from Datas import TypePlacement,HistoriquePlacement
from DateTableWidgetItem import CustomDateEdit
from GestionBD import DeleteHistoriquePlacement, InsertHistoriquePlacement
from BaseDialog import BaseDialog

def get_float_value(field: QLineEdit) -> float:
    text = field.text().replace(' ', '').replace(',', '.')
    return float(text) if text.replace('.', '', 1).isdigit() else 0.0

class AddEditPlacementDialog(BaseDialog):
    def __init__(self, parent=None, placement: HistoriquePlacement = None, mode: str = "edit"):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un Placement")

        self.placement = placement
        self.mode = mode.lower()  # "edit" ou "actualiser"

        self.layout = QFormLayout()

        # Nom (modifiable)
        self.nom = QLineEdit(self)

        # Type (lecture seule si modification)
        self.type = QComboBox(self)
        self.type.setEnabled(placement is None)
        for t in TypePlacement.return_list():
            self.type.addItem(t)

        # Date (lecture seule si modification)
        self.date = CustomDateEdit(self)
        self.date.setDate(QDate.currentDate())

        # Valeur actualisée (lecture seule si modification)
        self.val_actualisee = QLineEdit(self)
        self.val_actualisee.setReadOnly(placement is not None)
        self.val_actualisee.textEdited.connect(lambda: self.format_montant(self.val_actualisee))

        self.layout.addRow(QLabel("Nom:"), self.nom)
        self.layout.addRow(QLabel("Type:"), self.type)
        self.layout.addRow(QLabel("Date:"), self.date)
        self.layout.addRow(QLabel("Valeur actualisée:"), self.val_actualisee)

        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

        if self.placement:
            self.load_placement()

    def load_placement(self):
        self.nom.setText(self.placement.nom)

        # Désactiver les autres champs sauf le nom
        self.type.setCurrentText(self.placement.type)
        self.type.setDisabled(True)

        date = QDate.fromString(self.placement.date, 'dd/MM/yyyy')
        if date.isValid():
            self.date.setDate(date)
        if self.mode in ["actualiser","modifier"]:
            self.nom.setEnabled(False)
            self.date.setEnabled(True)
            self.val_actualisee.setReadOnly(False)
        else:
            self.date.setDisabled(True)
            self.val_actualisee.setText(self.placement.val_actualise)
            self.val_actualisee.setReadOnly(True)

    def submit(self):
        nom = self.nom.text()

        if not nom:
            QMessageBox.warning(self, "Erreur", "Le champ nom doit être rempli.")
            return

        if self.placement and self.mode == "edit":
            old_nom = self.placement.nom
            self.placement.nom = nom
            self.parent().update_placement(self.placement, old_nom)
            self.accept()
        elif self.placement and self.mode in ["actualiser","modifier"]:
            type = self.type.currentText()
            date = int(self.date.date().toString("yyyyMMdd"))
            valeur_actualisee = get_float_value(self.val_actualisee)
            new_placement = HistoriquePlacement(nom, type, date, valeur_actualisee, "Actualisation")
            DeleteHistoriquePlacement(nom,date)

            if InsertHistoriquePlacement(new_placement):
                self.parent().account_list.clear()
                self.parent().load_accounts()
                self.parent().compte_table.clearContents()
                self.parent().load_comptes()
                self.accept()

        else:
            type = self.type.currentText()
            date = int(self.date.date().toString("yyyyMMdd"))
            valeur_actualisee = get_float_value(self.val_actualisee)
            new_placement = HistoriquePlacement(nom, type, date, valeur_actualisee, "Création")
            
            self.parent().add_placement(new_placement)
            self.accept()

    def format_montant(self, field: QLineEdit):
        text = field.text()
        clean_text = ''.join(c for c in text if c.isdigit() or c == '.')
        if not clean_text:
            formatted = ""
        elif '.' in clean_text:
            partie_entiere, partie_decimale = clean_text.split('.', 1)
            partie_entiere = "{:,}".format(int(partie_entiere)).replace(",", " ")
            formatted = partie_entiere + '.' + partie_decimale
        else:
            formatted = "{:,}".format(int(clean_text)).replace(",", " ")

        field.blockSignals(True)
        field.setText(formatted)
        field.blockSignals(False)
        field.setCursorPosition(len(formatted))

    def format_montant_str(self, text: str):
        clean_text = ''.join(c for c in text if c.isdigit() or c == '.')
        if not clean_text:
            formatted = ""
        elif '.' in clean_text:
            partie_entiere, partie_decimale = clean_text.split('.', 1)
            partie_entiere = "{:,}".format(int(partie_entiere)).replace(",", " ")
            formatted = partie_entiere + '.' + partie_decimale
        else:
            formatted = "{:,}".format(int(clean_text)).replace(",", " ")