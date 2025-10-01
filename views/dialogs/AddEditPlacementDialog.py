from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QEvent, QDate
from models import TypePlacement,HistoriquePlacement
from utils.DateTableWidgetItem import CustomDateEdit
from database.gestion_bd import DeleteHistoriquePlacement, InsertHistoriquePlacement
from views.dialogs.BaseDialog import BaseDialog
import re
from datetime import datetime
from utils.GetPlacementValue import GetLastValuePlacement

def get_float_value(field: QLineEdit) -> float:
    text = field.text().replace(' ', '').replace(',', '.')
    return float(text) if text.replace('.', '', 1).isdigit() else 0.0



class AddEditPlacementDialog(BaseDialog):
    def check_disable_val_actualisee(self):
        if self.ticker.text().strip():  # Si le champ n'est pas vide
            self.label_val_actualise.hide()
            self.val_actualisee.hide()
        else:
            self.label_val_actualise.show()
            self.val_actualisee.show()
    def __init__(self, parent=None, placement: HistoriquePlacement = None, mode: str = "edit"):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un Placement")

        self.placement = placement
        self.mode = mode.lower()  # "edit" ou "actualiser"

        self.layout = QFormLayout()

        # Nom (modifiable)
        self.nom = QLineEdit(self)
        self.ticker = QLineEdit(self)
        self.ticker.textChanged.connect(self.check_disable_val_actualisee)

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
        self.layout.addRow(QLabel("N° ISIN:"), self.ticker)
        self.layout.addRow(QLabel("Type:"), self.type)
        self.layout.addRow(QLabel("Date:"), self.date)
        self.label_val_actualise = QLabel("Valeur actualisée:")
        self.layout.addRow(self.label_val_actualise, self.val_actualisee)


        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)
        self.date.setFocus()
        self.setLayout(self.layout)

        if self.placement:
            self.load_placement()

    def load_placement(self):
        self.nom.setText(self.placement.nom)
        self.ticker.setText(self.placement.ticker)

        # Désactiver les autres champs sauf le nom
        self.type.setCurrentText(self.placement.type)
        self.type.setDisabled(True)

        date = QDate.fromString(str(self.placement.date), 'dd/MM/yyyy')
        if date.isValid():
            self.date.setDate(date)
        if self.mode in ["actualiser","modifier"]:
            self.nom.setEnabled(False)
            self.date.setEnabled(True)
            self.val_actualisee.setReadOnly(False)
            if self.mode == "actualiser":
                self.ticker.setEnabled(False)
            else:
                self.ticker.setEnabled(True)
        else:
            self.date.setDisabled(True)
            self.val_actualisee.setText(str(self.placement.val_actualise))
            self.val_actualisee.setReadOnly(True)

    def submit(self):
        nom = self.nom.text()
        ticker = self.ticker.text()
        date = int(self.date.date().toString("yyyyMMdd"))

        if not nom:
            QMessageBox.warning(self, "Erreur", "Le champ nom doit être rempli.")
            return
        if ticker != "" and not re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",ticker):
            QMessageBox.warning(self, "Erreur", "Le numéro ISIN n'est pas valide.")
            return
        
        if ticker != "" and date > int(datetime.today().strftime("%Y%m%d")):
            QMessageBox.warning(self, "Erreur", "La date demandée pour le n° ISIN est dans le futur.")
            return

        if self.placement and self.mode == "edit":
            old_nom = self.placement.nom
            self.placement.nom = nom
            self.placement.ticker = ticker
            self.parent().update_placement(self.placement, old_nom)
            self.accept()
        elif self.placement and self.mode in ["actualiser","modifier"]:
            type = self.type.currentText()
            
            if ticker != "":
                try : 

                    values = GetLastValuePlacement(self.placement.ticker,datetime.strptime(str(date), "%Y%m%d").strftime("%Y-%m-%d"))
                    valeur_actualisee = values[self.placement.ticker][1]
                    self.val_actualisee.setText(str(valeur_actualisee))
                    date = values[self.placement.ticker][0]

                except KeyError:
                    QMessageBox.critical(self,"Erreur lors de la récuparation des données boursières",f"Impossible de récupérer la valeur du n° ISIN {ticker} dans les 100 derniers jours, données sans doutes indisponibles")
                    return
            else:    
                valeur_actualisee = get_float_value(self.val_actualisee)
            self.new_placement = HistoriquePlacement(nom, type, date, valeur_actualisee, "Actualisation",ticker)
            DeleteHistoriquePlacement(nom,date)

            if InsertHistoriquePlacement(self.new_placement):
                self.parent().account_list.clear()
                self.parent().load_accounts()
                self.parent().compte_table.clearContents()
                self.parent().load_comptes()
                self.accept()

        else:
            type = self.type.currentText()
            date = int(self.date.date().toString("yyyyMMdd"))
            valeur_actualisee = get_float_value(self.val_actualisee)
            self.new_placement = HistoriquePlacement(nom, type, date, valeur_actualisee, "Création",ticker)
            
            self.parent().add_placement(self.new_placement)
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