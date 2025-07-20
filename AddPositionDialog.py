from PyQt6.QtWidgets import (
    QPushButton, QLabel, QCheckBox, QLineEdit, QFormLayout, QMessageBox,QComboBox
)
from PyQt6.QtCore import QDate,Qt
from DateTableWidgetItem import CustomDateEdit
from datetime import *
from AddEditOperationDialog import get_next_echeance
from BaseDialog import BaseDialog

from GestionBD import *

class AddPositionDialog(BaseDialog):
    def __init__(self, parent=None, account_id=None, isEcheance = False, echeance = None, compte_choisi_id = None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une nouvelle position")
        self.account_id = account_id
        self.isEcheance = isEcheance
        self.echeance = echeance
        self.compte_choisi_id = compte_choisi_id

        # Layout pour la pop-up
        self.layout = QFormLayout()

        self.date = CustomDateEdit()
        self.date.setDate(QDate.currentDate())
        # Création de la QComboBox pour le type de compte
        self.type_placement = QComboBox(self)
        for type_placement in TypePosition.return_list():
            self.type_placement.addItem(type_placement)

        self.compte_associe = QComboBox(self)
        comptes = GetComptesExceptCurrent(self.account_id)
        for compte in comptes:
            self.compte_associe.addItem(compte.nom, userData=str(compte._id))

        self.placement = QComboBox(self)
        self.placement.currentTextChanged.connect(self.set_last_val_part)
        placements = GetLastPlacement()
        self.val_part = QLineEdit(self)
        for placement in placements:
            self.placement.addItem(placement.nom)

        self.nb_part = QLineEdit(self)     
        self.frais = QLineEdit(self)
        self.interet = QLineEdit(self)     
        self.notes = QLineEdit(self)

        # Checkbox pour ajouter à l’échéancier
        self.ajouter_echeancier_checkbox = QCheckBox("Ajouter à l’échéancier", self)
        self.ajouter_echeancier_checkbox.stateChanged.connect(self.on_toggle_echeancier_fields)

        # Widgets pour fréquence et date de première échéance
        self.label_frequence = QLabel("Fréquence:")
        self.frequence = QComboBox(self)
        self.frequence.addItems([f for f in FrequenceEcheancier.return_list()])

        self.label_date_premiere = QLabel("Première échéance:")
        self.date_premiere = CustomDateEdit()
        self.date_premiere.setDate(QDate.currentDate())

        self.set_echeancier_fields_visible(False)

        self.nb_part.textEdited.connect(lambda: self.format_montant(self.nb_part))
        self.val_part.textEdited.connect(lambda: self.format_montant(self.val_part))
        self.frais.textEdited.connect(lambda: self.format_montant(self.frais))
        self.interet.textEdited.connect(lambda: self.format_montant(self.interet))





        self.layout.addRow(QLabel("Date:"),self.date)
        self.label_compte_associe = QLabel("Compte Associé:")
        self.layout.addRow(self.label_compte_associe, self.compte_associe)
        self.layout.addRow(QLabel("Type:"), self.type_placement)
        self.layout.addRow(QLabel("Placement:"), self.placement)
        self.layout.addRow(QLabel("Nombre de part:"), self.nb_part)
        self.layout.addRow(QLabel("Valeur de la part:"), self.val_part)
        self.layout.addRow(QLabel("Frais:"), self.frais) 
        self.layout.addRow(QLabel("Interêts:"), self.interet)
        self.layout.addRow(QLabel("Notes:"), self.notes)
        self.layout.addRow(self.ajouter_echeancier_checkbox)
        self.layout.addRow(self.label_frequence, self.frequence)
        self.layout.addRow(self.label_date_premiere, self.date_premiere)
        

        # Bouton pour ajouter le compte
        self.add_button = QPushButton("Ajouter Position", self)
        self.add_button.clicked.connect(self.add_position)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)
        self.type_placement.currentTextChanged.connect(self.on_type_operation_changed)
        self.on_type_operation_changed(self.type_placement.currentText())

        if self.isEcheance:
            self.ajouter_echeancier_checkbox.setCheckState(Qt.CheckState.Checked)
            self.ajouter_echeancier_checkbox.setEnabled(False)


    def set_last_val_part(self, placement_name):
        last_val = GetLastValueForPlacement(placement_name)
        if last_val is not None:
            formatted = "{:,.2f}".format(last_val).replace(",", " ").replace(".", ",")
            self.val_part.setText(formatted)
            
    def add_position(self):

        def get_float_value(field: QLineEdit) -> float:
            text = field.text().replace(' ', '').replace(',', '.')
            try:
                return float(text)
            except ValueError:
                return 0.0 
        # Récupérer les données saisies
        compte_associe_id = self.compte_associe.currentData()
        nom_placement = self.placement.currentText()
        nb_part = get_float_value(self.nb_part)
        val_part = get_float_value(self.val_part)
        frais = get_float_value(self.frais)
        interets = get_float_value(self.interet)
        date = int(self.date.date().toString("yyyyMMdd"))
        notes = self.notes.text()
        montant_investit = 0
        type_placement = self.type_placement.currentText()
        if type_placement in [TypePosition.Vente.value,TypePosition.Perte.value]:
            nb_part *= -1

        # Appliquer la logique "compte associé" seulement si c'est un transfert
        if type_placement in ["Achat", "Intérêts","Vente"]:
            compte_associe_id = self.compte_associe.currentData()
            if type_placement == "Achat":
                montant_investit = round(nb_part*val_part + frais)
        else:
            compte_associe_id = ""

        if self.ajouter_echeancier_checkbox.isChecked():
            frequence = self.frequence.currentText()
            date_premiere = int(self.date_premiere.date().toString("yyyyMMdd"))
            prochaine_echeance = get_next_echeance(date_premiere, frequence)
            compte_id = None
            if self.echeance is not None:
                compte_id = self.echeance.compte_id
                prochaine_echeance = self.echeance.prochaine_echeance
            elif self.compte_choisi_id is not None:
                compte_id = self.compte_choisi_id
            else:
                compte_id = self.account_id

            # Enregistrement dans la table des échéanciers
            echeance = Echeance(
                frequence,
                date_premiere,
                prochaine_echeance,
                type_placement,
                "",
                nom_placement,
                "",
                "",
                0,
                0,
                notes,
                compte_id,
                nb_part,
                val_part,
                frais,
                interets,
                "",
                1,
                compte_associe_id,
                "",
                ""
                # ajoute d’autres champs nécessaires selon la structure de Echeancier
            )
            InsertEcheance(echeance)
            self.parent().load_echeance()
        
        if self.account_id is not None:
            # Créer l'objet compte
            position = Position(date,type_placement,nom_placement,nb_part,val_part,frais,interets, notes,self.account_id,montant_investit,compte_associe_id)

            # Ajouter le compte dans la base de données SQLite
            self.parent().add_position(position)

            # Fermer la pop-up après ajout
        self.accept()
   


    def on_type_operation_changed(self, new_type_operation):
        if new_type_operation in ["Achat", "Intérêts","Vente"]:
            self.label_compte_associe.show()
            self.compte_associe.show()
        else:
            self.label_compte_associe.hide()
            self.compte_associe.hide()

    def format_montant(self, field: QLineEdit):
        text = field.text().strip()

        if text in ("", "-", "-.", "."):
            # Laisse l'utilisateur continuer à taper
            return

        # Garde le signe négatif uniquement s'il est au début
        is_negative = text.startswith('-')
        text = text[1:] if is_negative else text

        # Nettoyage : garder uniquement chiffres et le premier point
        result = []
        point_seen = False
        for c in text:
            if c.isdigit():
                result.append(c)
            elif c == '.' and not point_seen:
                result.append(c)
                point_seen = True

        clean_text = ''.join(result)

        if not clean_text:
            formatted = "-"
        elif '.' in clean_text:
            partie_entiere, partie_decimale = clean_text.split('.', 1)
            partie_entiere = "{:,}".format(int(partie_entiere or "0")).replace(",", " ")
            formatted = partie_entiere + '.' + partie_decimale
        else:
            formatted = "{:,}".format(int(clean_text)).replace(",", " ")

        if is_negative:
            formatted = '-' + formatted

        field.blockSignals(True)
        field.setText(formatted)
        field.blockSignals(False)
        field.setCursorPosition(len(formatted))

    def set_echeancier_fields_visible(self, visible: bool):
        self.label_frequence.setVisible(visible)
        self.frequence.setVisible(visible)
        self.label_date_premiere.setVisible(visible)
        self.date_premiere.setVisible(visible)

    def on_toggle_echeancier_fields(self):
        self.set_echeancier_fields_visible(self.ajouter_echeancier_checkbox.isChecked())

