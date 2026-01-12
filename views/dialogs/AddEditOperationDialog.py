from PyQt6.QtWidgets import (
    QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox,QComboBox,QCompleter,QCheckBox
)
from PyQt6.QtCore import Qt,QDate
from models import Operation,TypeOperation,Echeance
from views.dialogs.BaseDialog import BaseDialog
from utils.DateTableWidgetItem import CustomDateEdit
from datetime import *

from database.gestion_bd import *


def format_montant(field: QLineEdit):
    try:
        text = field.text().strip()
        cursor_pos = field.cursorPosition()  # position avant formatage

        # Gestion du signe négatif
        clean = ''.join(c for c in text if c.isdigit() or c == '.')

        if clean:
            if '.' in clean:
                ent, dec = clean.split('.', 1)
                ent = "{:,}".format(int(ent)).replace(",", " ")
                formatted = ent + '.' + dec
            else:
                formatted = "{:,}".format(int(clean)).replace(",", " ")

        # Mise à jour du champ sans relancer l’événement
        field.blockSignals(True)
        field.setText(formatted)
        field.blockSignals(False)

        # Réajustement de la position du curseur
        new_pos = min(cursor_pos, len(formatted))
        field.setCursorPosition(new_pos)

    except:
        pass


def get_next_echeance(date_premiere: int, frequence: str) -> int:
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    # Convertir yyyymmdd → datetime
    date_str = str(date_premiere)
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    
    # Ajouter le bon décalage selon la fréquence
    if frequence.lower() == "mensuelle":
        next_date = date_obj + relativedelta(months=1)
    elif frequence.lower() == "trimestrielle":
        next_date = date_obj + relativedelta(months=3)
    elif frequence.lower() == "semestrielle":
        next_date = date_obj + relativedelta(months=6)
    elif frequence.lower() == "annuelle":
        next_date = date_obj + relativedelta(years=1)
    else:
        raise ValueError(f"Fréquence non reconnue: {frequence}")

    # Reconvertir datetime → int yyyymmdd
    return int(next_date.strftime("%Y%m%d"))

def set_combobox_index_by_text(combo: QComboBox, text: str):
    index = combo.findText(text, Qt.MatchFlag.MatchExactly)
    if index >= 0:
        combo.setCurrentIndex(index)

def set_combobox_index_by_data(combo: QComboBox, data):
    index = combo.findData(data)
    if index >= 0:
        combo.setCurrentIndex(index)

class AddEditOperationDialog(BaseDialog):
    def __init__(self, parent=None, account_id=None, operation: Operation = None, isEdit=False, isEcheance = False, echeance:Echeance = None, compte_choisi_id = None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier une opération")       
        self.account_id = account_id
        self.operation = operation
        self.isEdit = isEdit
        self.isEcheance = isEcheance
        self.echeance = echeance
        self.compte_choisi_id = compte_choisi_id

        self.layout = QFormLayout()

        self.date = CustomDateEdit()
        self.date.setDate(QDate.currentDate())

        self.type_operation = QComboBox(self)
        for type_op in TypeOperation.return_list():
            self.type_operation.addItem(type_op)

        self.compte_associe = QComboBox(self)
        comptes = GetComptes(alphabetical=True)
        for compte in comptes:
            self.compte_associe.addItem(compte.nom, userData=str(compte._id))

        self.categorie = QComboBox(self)
        self.categorie.addItem("")
        for cat in GetCategorie():
            self.categorie.addItem(cat.nom)

        self.type_tier = QComboBox(self)
        types_tier = GetTypeTier()
        for t in types_tier:
            self.type_tier.addItem(t.nom)

        self.moyen_paiement = QComboBox(self)
        self.moyen_paiement.addItem("")
        for mp in GetMoyenPaiement():
            self.moyen_paiement.addItem(mp.nom)

        self.tier = QComboBox(self)
        self.tier.setEditable(True)
        if operation:
            tiers = GetTiersActifByType(operation.type_tier)
        else:
            tiers = GetTiersActifByType(types_tier[0].nom)
        self.tier_list = [t.nom for t in tiers]
        self.completer = QCompleter(self.tier_list, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.tier.setCompleter(self.completer)
        for t in tiers:
            self.tier.addItem(t.nom, userData=t._id)

        self.sous_categorie = QComboBox(self)
        self.update_sous_categories(self.categorie.currentText())
        self.categorie.currentTextChanged.connect(self.on_category_changed)

        self.num_cheque = QLineEdit(self)
        self.num_cheque.setText(GetNextNumCheque())
        self.num_cheque.textEdited.connect(lambda:format_montant(self.num_cheque))
        self.montant = QLineEdit(self)
        self.montant.textEdited.connect(lambda:format_montant(self.montant))
        self.notes = QLineEdit(self)

                # Checkbox pour ajouter un bénéficiaire
        self.ajouter_benef_checkbox = QCheckBox("Ajouter un bénéficiaire", self)
        self.ajouter_benef_checkbox.stateChanged.connect(self.on_toggle_beneficiaire_fields)

        # Combos pour type de bénéficiaire et bénéficiaire
        self.label_type_beneficiaire = QLabel("Type Bénéficiaire:")
        self.type_beneficiaire = QComboBox(self)

        self.label_beneficiaire = QLabel("Bénéficiaire:")
        self.beneficiaire = QComboBox(self)
        self.beneficiaire.setEditable(True)
        self.beneficiaire_completer = QCompleter([], self)
        self.beneficiaire.setCompleter(self.beneficiaire_completer)

        # Charger les types bénéficiaires
        types_beneficiaire = GetTypeBeneficiaire()
        for t in types_beneficiaire:
            self.type_beneficiaire.addItem(t.nom)

        # Connecter changement de type
        self.type_beneficiaire.currentTextChanged.connect(self.on_type_beneficiaire_changed)

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

        # Ajout au layout

        # Masquer les champs au départ
        self.set_echeancier_fields_visible(False)

        self.label_compte_associe = QLabel("Compte Associé:")
        self.label_type_operation = QLabel("Type:")
        self.label_type_tier = QLabel("Type Tiers:")
        self.label_tier = QLabel("Tiers:")
        self.label_moyen_paiement = QLabel("Moyen de Paiement:")
        self.label_num_cheque = QLabel("Numéro Chèque:")
        self.label_categorie = QLabel("Catégorie:")
        self.label_sous_categorie = QLabel("Sous Catégorie:")

        if self.echeance is None:
            self.layout.addRow(QLabel("Date:"), self.date)
        else :
            year = self.echeance.prochaine_echeance // 10000
            month = (self.echeance.prochaine_echeance // 100) % 100
            day = self.echeance.prochaine_echeance % 100
            self.date_prochaine_echeance = CustomDateEdit()
            self.date_prochaine_echeance.setDate(QDate(year, month, day))
            self.layout.addRow(QLabel("Prochaine échéance:"), self.date_prochaine_echeance)
        self.layout.addRow(self.label_type_operation, self.type_operation)
        self.layout.addRow(self.label_compte_associe, self.compte_associe)
        self.layout.addRow(self.label_type_tier, self.type_tier)
        self.layout.addRow(self.label_tier, self.tier)
        self.layout.addRow(self.label_moyen_paiement, self.moyen_paiement)
        self.layout.addRow(self.label_num_cheque, self.num_cheque)
        self.layout.addRow(self.label_categorie, self.categorie)
        self.layout.addRow(self.label_sous_categorie, self.sous_categorie)
        self.layout.addRow(QLabel("Montant:"), self.montant)
        self.layout.addRow(QLabel("Notes:"), self.notes)
        self.layout.addRow(self.ajouter_benef_checkbox)
        self.layout.addRow(self.label_type_beneficiaire, self.type_beneficiaire)
        self.layout.addRow(self.label_beneficiaire, self.beneficiaire)
        self.layout.addRow(self.ajouter_echeancier_checkbox)
        self.layout.addRow(self.label_frequence, self.frequence)
        self.layout.addRow(self.label_date_premiere, self.date_premiere)

        # Cacher par défaut
        self.set_beneficiaire_fields_visible(False)

        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

        self.tier.currentTextChanged.connect(self.on_tier_changed)
        self.type_tier.currentTextChanged.connect(self.on_type_tier_changed)
        self.type_operation.currentTextChanged.connect(self.on_type_operation_changed)
        self.moyen_paiement.currentTextChanged.connect(self.on_moyen_paiement_changed)

        self.date.setFocus()

        self.on_type_operation_changed(self.type_operation.currentText())
        self.on_moyen_paiement_changed(self.moyen_paiement.currentText())

        if self.operation:
            self.fill_fields()

        if self.echeance:
            self.fill_fields()
            self.fill_fields_echeance()

        if self.isEcheance:
            self.ajouter_echeancier_checkbox.setCheckState(Qt.CheckState.Checked)
            self.ajouter_echeancier_checkbox.setEnabled(False)


    def set_beneficiaire_fields_visible(self, visible: bool):
        self.label_type_beneficiaire.setVisible(visible)
        self.type_beneficiaire.setVisible(visible)
        self.label_beneficiaire.setVisible(visible)
        self.beneficiaire.setVisible(visible)

    def on_toggle_beneficiaire_fields(self):
        self.set_beneficiaire_fields_visible(self.ajouter_benef_checkbox.isChecked())
        if self.ajouter_benef_checkbox.isChecked():
            self.on_type_beneficiaire_changed(self.type_beneficiaire.currentText())

    def set_echeancier_fields_visible(self, visible: bool):
        self.label_frequence.setVisible(visible)
        self.frequence.setVisible(visible)
        self.label_date_premiere.setVisible(visible)
        self.date_premiere.setVisible(visible)

    def on_toggle_echeancier_fields(self):
        self.set_echeancier_fields_visible(self.ajouter_echeancier_checkbox.isChecked())

    def on_type_beneficiaire_changed(self, type_benef):
        beneficiaires = GetBeneficiairesByType(type_benef)
        self.beneficiaire.clear()
        self.beneficiaire_list = [b.nom for b in beneficiaires]
        self.beneficiaire_completer = QCompleter(self.beneficiaire_list, self)
        self.beneficiaire_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.beneficiaire_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.beneficiaire.setCompleter(self.beneficiaire_completer)
        for b in beneficiaires:
            self.beneficiaire.addItem(b.nom, userData=b.nom)

    def fill_fields_echeance(self):
        self.date_premiere.setDate(QDate.fromString(str(self.echeance.echeance1), "yyyyMMdd"))
        set_combobox_index_by_text(self.frequence, self.echeance.frequence)

    def fill_fields(self):
        self.date.setDate(QDate.fromString(str(self.operation.date), "yyyyMMdd"))
        self.on_type_tier_changed(self.operation.type_tier)
        set_combobox_index_by_text(self.type_operation, self.operation.type)
        set_combobox_index_by_text(self.type_tier, self.operation.type_tier)
        set_combobox_index_by_data(self.tier, self.operation.tier)
        if self.operation.type_beneficiaire != "" and self.operation.beneficiaire != "":
           self.ajouter_benef_checkbox.setCheckState(Qt.CheckState.Checked)
           set_combobox_index_by_text(self.type_beneficiaire, self.operation.type_beneficiaire)
           set_combobox_index_by_text(self.beneficiaire, self.operation.beneficiaire)     

        # ComboBox tier (editable avec userData)
        if self.operation.tier == '':
            self.moyen_paiement.setCurrentText("")
            self.categorie.setCurrentText("")
            self.sous_categorie.setCurrentText("")            
        else:
            tier = GetTierById(self.operation.tier) or ""
            self.moyen_paiement.setCurrentText(self.operation.moyen_paiement)
            self.categorie.setCurrentText(self.operation.categorie)
            self.sous_categorie.setCurrentText(self.operation.sous_categorie)
            self.tier.setCurrentText(tier.nom)
            
        self.num_cheque.setText(str(self.operation.num_cheque))
        # self.update_sous_categories(self.operation.categorie)

        montant = self.operation.credit or self.operation.debit or 0
        self.montant.setText("{:,.2f}".format(abs(montant)).replace(",", " "))
        self.notes.setText(self.operation.notes or "")

        if self.operation.compte_associe:
            set_combobox_index_by_data(self.compte_associe, self.operation.compte_associe)

    def submit(self):
        operation = None
        id_tier = str(self.tier.currentData())
        if id_tier == 'None':
            id_tier = ""
        tier = self.tier.currentText()
        type_operation = self.type_operation.currentText()
        if type_operation in ["Débit","Crédit"]:
            type_tier = self.type_tier.currentText()
        else :
            type_tier = ""
        moyen_paiement = self.moyen_paiement.currentText()
        num_cheque = self.num_cheque.text()
        compte_associe = self.compte_associe.currentData()
        if self.echeance is None:
            date = int(self.date.date().toString("yyyyMMdd"))
        else :
            date = int(self.date_prochaine_echeance.date().toString("yyyyMMdd"))
        notes = self.notes.text()
        categorie = self.categorie.currentText()
        sous_categorie = self.sous_categorie.currentText()
        montant = self.montant.text().replace(" ", "")
        debit = credit = 0
        type_beneficiaire = self.type_beneficiaire.currentText()
        beneficiaire = self.beneficiaire.currentText()
        frequence = self.frequence.currentText()

        if type_operation in ["Transfert vers", "Transfert de"]:
            compte_associe = self.compte_associe.currentData()
        else :
            compte_associe = ""

        if not self.ajouter_benef_checkbox.isChecked():
            type_beneficiaire = ""
            beneficiaire = ""

        if self.account_id == compte_associe and not self.isEcheance:
            QMessageBox.warning(self, "Erreur", "Le compte associé ne peut pas être le compte actuel")
            return

        if (not date or not type_operation or not montant or not tier) and type_operation not in ["Transfert vers", "Transfert de"]:
            QMessageBox.warning(self, "Erreur", "Les champs Date, Type, Tier et Montant doivent être remplis.")
            return
        if tier not in self.tier_list and type_operation not in ["Transfert vers", "Transfert de"]:
            t = Tier(tier,type_tier,categorie,sous_categorie,moyen_paiement)
            id_tier = str(t._id)
            InsertTier(t)
            self.parent().load_tiers()
        if self.ajouter_benef_checkbox.isChecked():
            if  beneficiaire not in self.beneficiaire_list:
                b = Beneficiaire(beneficiaire,type_beneficiaire)
                InsertBeneficiaire(b)
                self.parent().load_beneficiaire()
        try:
            if type_operation not in ['Débit', 'Transfert vers']:
                montant = float(montant)
                credit = montant
            else:
                montant = float(montant) * -1
                debit = montant
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le montant doit être un nombre.")
            return
        
        if not self.isEcheance:
            if self.operation:
                # Mise à jour
                old_debit = self.operation.debit
                old_credit = self.operation.credit
                self.operation.date = date
                self.operation.type = type_operation
                self.operation.type_tier = type_tier
                self.operation.tier = id_tier
                self.operation.moyen_paiement = moyen_paiement
                self.operation.num_cheque = num_cheque
                self.operation.categorie = categorie
                self.operation.sous_categorie = sous_categorie
                self.operation.debit = debit
                self.operation.credit = credit
                self.operation.notes = notes
                self.operation.compte_associe = compte_associe
                self.operation.beneficiaire = beneficiaire
                self.operation.type_beneficiaire = type_beneficiaire
                self.parent().update_operation(self.operation,old_credit,old_debit,self.isEdit)
            elif self.operation is None :
                # Insertion
                operation = Operation(date, type_operation, type_tier, id_tier, moyen_paiement, categorie, sous_categorie,
                                        debit, credit, notes, self.account_id, num_cheque, compte_associe,type_beneficiaire=type_beneficiaire,beneficiaire=beneficiaire)
                self.parent().add_operation(operation)

        if type_operation in ["Transfert vers", "Transfert de"] and not self.isEcheance :
            compte_associe = self.compte_associe.currentData()
            if type_operation == "Transfert vers":
                type_op_associe = "Transfert de"
                debit_associe = 0
                credit_associe = debit * -1
            else:
                type_op_associe = "Transfert vers"
                debit_associe = credit * -1
                credit_associe = 0
            if GetCompteType(compte_associe) in ["Courant", "Epargne"]:
                o = Operation(date, type_op_associe, "", "", "", "", "", debit_associe, credit_associe, "", compte_associe, "", self.account_id,type_beneficiaire=type_beneficiaire,beneficiaire=beneficiaire)
                if operation is None:
                    operation = self.operation
                if self.isEdit:
                    o._id = operation.link
                    old_operation = GetOperation(o._id)
                    DeleteOperation(o,old_operation.credit,old_operation.debit)
                else:
                    o.link = str(operation._id)
                    operation.link = str(o._id)
                InsertOperation(o)
                UpdateOperationLink(operation)
                self.parent().account_list.clear()
                self.parent().load_accounts()
            type_tier = id_tier = moyen_paiement = categorie = sous_categorie = ""
        if type_operation not in ["Transfert vers", "Transfert de"]:
            compte_associe = ""

        
        if self.ajouter_echeancier_checkbox.isChecked():
            frequence = self.frequence.currentText()
            date_premiere = int(self.date_premiere.date().toString("yyyyMMdd"))
            prochaine_echeance = get_next_echeance(date_premiere, frequence)
            compte_id = None
            if self.echeance is not None:
                compte_id = self.echeance.compte_id
                if self.echeance.echeance1 == self.date_premiere or (self.isEdit and self.isEcheance):
                    prochaine_echeance = self.echeance.prochaine_echeance
                if date != prochaine_echeance:
                    prochaine_echeance = date

            elif self.compte_choisi_id is not None:
                compte_id = self.compte_choisi_id
            else:
                compte_id = self.account_id

            # Enregistrement dans la table des échéanciers
            echeance = Echeance(
                frequence,
                date_premiere,
                prochaine_echeance,
                type_operation,
                type_tier,
                id_tier,
                categorie,
                sous_categorie,
                debit,
                credit,
                notes,
                compte_id,
                0,
                0,
                0,
                0,
                moyen_paiement,
                0,
                compte_associe,
                type_beneficiaire,
                beneficiaire
                # ajoute d’autres champs nécessaires selon la structure de Echeancier
            )
            if self.isEcheance:
                if self.isEdit:
                    echeance._id = self.operation._id
                    echeance.compte_id = self.echeance.compte_id
                    UpdateEcheance(echeance)
                else:
                    if echeance.echeance1 > int(datetime.date.today().strftime("%Y%m%d")):
                        echeance.prochaine_echeance = echeance.echeance1
                    
                    else:
                        operation = Operation(date_premiere, type_operation, type_tier, id_tier, moyen_paiement, categorie, sous_categorie,
                                                debit, credit, notes, compte_id, num_cheque, compte_associe,type_beneficiaire=type_beneficiaire,beneficiaire=beneficiaire)
                        self.parent().add_operation(operation)
                    InsertEcheance(echeance)
            else:
                if echeance.echeance1 > int(datetime.date.today().strftime("%Y%m%d")):
                    echeance.prochaine_echeance = echeance.echeance1
                InsertEcheance(echeance)
            self.parent().load_echeance()
        self.accept()

    def on_category_changed(self, category):
        self.update_sous_categories(category)

    def update_sous_categories(self, category):
        self.sous_categorie.clear()
        self.sous_categorie.addItem("")
        for sc in GetSousCategorie(category):
            self.sous_categorie.addItem(sc.nom)

    def on_tier_changed(self, new_tier_name):
        match = next((t for t in GetTiersActif() if t.nom == new_tier_name), None)
        if match:
            index_mp = self.moyen_paiement.findText(match.moyen_paiement)
            if index_mp >= 0:
                self.moyen_paiement.setCurrentIndex(index_mp)
            index_cat = self.categorie.findText(match.categorie)
            if index_cat >=0:
                self.categorie.setCurrentIndex(index_cat)
            index_sous_cat = self.sous_categorie.findText(match.sous_categorie)
            if index_sous_cat >=0:
                self.sous_categorie.setCurrentIndex(index_sous_cat)

    def on_type_tier_changed(self, new_type):
        tiers = GetTiersActifByType(new_type)
        self.tier_list = [t.nom for t in tiers]
        self.tier.clear()
        self.completer = QCompleter(self.tier_list, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.tier.setCompleter(self.completer)
        for t in tiers:
            self.tier.addItem(t.nom, userData=t._id)

    def on_type_operation_changed(self, new_type):
        is_transfer = new_type in ["Transfert vers", "Transfert de"]
        self.label_compte_associe.setVisible(is_transfer)
        self.compte_associe.setVisible(is_transfer)
        for label, widget in [
            (self.label_type_tier, self.type_tier),
            (self.label_tier, self.tier),
            (self.label_moyen_paiement, self.moyen_paiement),
            (self.label_categorie, self.categorie),
            (self.label_sous_categorie, self.sous_categorie),
        ]:
            label.setVisible(not is_transfer)
            widget.setVisible(not is_transfer)

    def on_moyen_paiement_changed(self, moyen):
        is_cheque = moyen == "Chèque"
        self.num_cheque.setText("")
        if is_cheque:            
            self.num_cheque.setText(GetNextNumCheque())
        self.label_num_cheque.setVisible(is_cheque)
        self.num_cheque.setVisible(is_cheque)
