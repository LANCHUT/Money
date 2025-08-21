from PyQt6.QtWidgets import (
    QPushButton, QLabel, QCheckBox, QLineEdit, QFormLayout, QMessageBox,QComboBox
)
from PyQt6.QtCore import QDate,Qt
from DateTableWidgetItem import CustomDateEdit
from datetime import *
from AddEditOperationDialog import get_next_echeance
from BaseDialog import BaseDialog

from GestionBD import *

class AddEditPositionDialog(BaseDialog):
    def __init__(self, parent=None,account_id=None, position:Position = None, isEcheance = False, echeance = None, compte_choisi_id = None, isEdit = False):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une nouvelle position")
        self.account_id = account_id
        self.position = position
        self.isEcheance = isEcheance
        self.echeance = echeance
        self.compte_choisi_id = compte_choisi_id
        self.isEdit = isEdit

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
        if self.position:

            self.fill_fields()

        self.set_echeancier_fields_visible(False)

        self.nb_part.textEdited.connect(lambda: self.format_montant(self.nb_part))
        self.val_part.textEdited.connect(lambda: self.format_montant(self.val_part))
        self.frais.textEdited.connect(lambda: self.format_montant(self.frais))
        self.interet.textEdited.connect(lambda: self.format_montant(self.interet))





        self.layout.addRow(QLabel("Date:"),self.date)
        self.layout.addRow(QLabel("Type:"), self.type_placement)
        self.label_compte_associe = QLabel("Compte Associé:")
        self.layout.addRow(self.label_compte_associe, self.compte_associe)
        self.layout.addRow(QLabel("Placement:"), self.placement)
        self.label_nb_part = QLabel("Nombre de part:")
        self.layout.addRow(self.label_nb_part, self.nb_part)
        self.label_val_part = QLabel("Valeur de la part:")
        self.layout.addRow(self.label_val_part, self.val_part)
        self.label_frais = QLabel("Frais:")
        self.layout.addRow(self.label_frais, self.frais)
        self.label_interets = QLabel("Interêts:")
        self.layout.addRow(self.label_interets, self.interet)
        self.label_notes = QLabel("Notes:")
        self.layout.addRow(self.label_notes, self.notes)
        self.layout.addRow(self.ajouter_echeancier_checkbox)
        self.layout.addRow(self.label_frequence, self.frequence)
        self.layout.addRow(self.label_date_premiere, self.date_premiere)
        

        # Bouton pour ajouter le compte
        self.add_button = QPushButton("Valider", self)
        self.add_button.clicked.connect(self.add_position)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)
        self.type_placement.currentTextChanged.connect(self.on_type_operation_changed)
        self.on_type_operation_changed(self.type_placement.currentText())

        self.date.setFocus()

        if self.isEcheance:
            self.ajouter_echeancier_checkbox.setCheckState(Qt.CheckState.Checked)
            self.ajouter_echeancier_checkbox.setEnabled(False)
            if self.isEdit:
                self.frequence.setCurrentText(echeance.frequence)
                self.date_premiere.setDate(QDate(QDate.fromString(str(self.echeance.echeance1),"yyyyMMdd")))
       



    def set_last_val_part(self, placement_name):
        last_val = GetLastValueForPlacement(placement_name)
        if last_val is not None:
            formatted = "{:,.4f}".format(last_val).replace(",", " ").replace(".", ",")
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
        type_placement = self.type_placement.currentText()
        if nb_part == 0 and type_placement not in [TypePosition.Interet.value]:
            QMessageBox.warning(self, "Erreur", "Le champs nb_part doit être remplis.")
            return
        if type_placement in [TypePosition.Vente.value,TypePosition.Perte.value]:
            nb_part *= -1

        if nb_part < 0 and type_placement in [TypePosition.Gain.value,TypePosition.Achat.value,TypePosition.Don.value]:
            nb_part *= -1

        # Appliquer la logique "compte associé" seulement si c'est un transfert
        if type_placement in ["Achat", "Intérêts","Vente"]:
            compte_associe_id = self.compte_associe.currentData()
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
            
            if self.isEcheance: 
                if not self.isEdit:
                    if echeance.echeance1 > int(datetime.date.today().strftime("%Y%m%d")):
                        echeance.prochaine_echeance = echeance.echeance1
                    else:
                        position = Position(date_premiere,type_placement,nom_placement,nb_part,val_part,frais,interets, notes,compte_id,round((nb_part*nb_part + frais),2),compte_associe_id)
                        self.parent().add_position(position)
                else:
                    echeance._id = self.position._id
                    echeance.compte_id = self.echeance.compte_id
                    DeleteEcheance(echeance._id)
            if echeance.echeance1 > int(datetime.date.today().strftime("%Y%m%d")):
                    echeance.prochaine_echeance = echeance.echeance1
            InsertEcheance(echeance)         
            self.parent().load_echeance()
        
        if not self.isEcheance:
            if self.position:
                # Mise à jour
                self.position.date = date
                self.position.type = type_placement
                self.position.nom_placement = nom_placement
                self.position.nb_part = nb_part
                self.position.val_part = val_part
                self.position.frais = frais
                self.position.interets = interets
                self.position.notes = notes
                self.position.compte_associe = compte_associe_id
                self.parent().update_position(self.position,self.isEdit)
            elif self.position is None :
                # Créer l'objet compte
                position = Position(date,type_placement,nom_placement,nb_part,val_part,frais,interets, notes,self.account_id,round((nb_part*nb_part + frais),2),compte_associe_id)
                self.parent().add_position(position)
        self.accept()
   


    def on_type_operation_changed(self, new_type_operation):
        if new_type_operation in ["Achat", "Intérêts","Vente"]:
            if new_type_operation == "Intérêts":
                self.label_nb_part.hide()
                self.nb_part.hide()
                self.label_val_part.hide()
                self.val_part.hide()
                self.label_frais.hide()
                self.frais.hide()

            else:
                self.label_nb_part.show()
                self.nb_part.show()
                self.label_val_part.show()
                self.val_part.show()
                self.label_frais.show()
                self.frais.show()

            self.label_compte_associe.show()
            self.compte_associe.show()
        else:
            self.label_compte_associe.hide()
            self.compte_associe.hide()
            self.label_nb_part.show()
            self.nb_part.show()
            self.label_val_part.show()
            self.val_part.show()
            self.label_frais.show()
            self.frais.show()

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

    def fill_fields(self):
        from AddEditOperationDialog import set_combobox_index_by_text,set_combobox_index_by_data
        self.date.setDate(QDate.fromString(str(self.position.date), "yyyyMMdd"))
        set_combobox_index_by_text(self.type_placement, self.position.type)
        set_combobox_index_by_text(self.placement, self.position.nom_placement)
        self.val_part.setText(str(self.position.val_part))
        self.nb_part.setText(str(self.position.nb_part))
        self.frais.setText(str(self.position.frais))
        self.interet.setText(str(self.position.interets))
        self.notes.setText(self.position.notes)

        if self.position.compte_associe:
            set_combobox_index_by_data(self.compte_associe, self.position.compte_associe)

