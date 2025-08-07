# AddEditLoanDialog.py

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QComboBox, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QHeaderView, QAbstractItemView
)
from DateTableWidgetItem import CustomDateEdit
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QDoubleValidator, QIntValidator

from BaseDialog import BaseDialog # Votre classe de base pour les dialogues
from Datas import Loan
from datetime import date # Pour travailler avec les dates Python


class AddEditLoanDialog(BaseDialog):
    def __init__(self, parent=None, loan: Loan = None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un Prêt")
        self.setMinimumWidth(500) # Augmenter la largeur pour plus de confort

        self.loan = loan
        self.taux_variables_data = [] # Pour stocker les données du tableau de taux variables

        # Valideurs pour les champs numériques
        self.int_validator = QIntValidator(1, 1000, self) # Durée en années (ex: 1 à 1000 ans)
        self.double_validator = QDoubleValidator(0.0, 999999999.0, 2, self) # Montants (solde, assurance)
        self.taux_validator = QDoubleValidator(0.0, 1.0, 5, self) # Taux (0.00000 à 1.00000)

        # Layout principal
        self.main_layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        # --- Champs communs du prêt ---
        self.nom_input = QLineEdit(self)
        self.montant_initial_input = QLineEdit(self)
        self.montant_initial_input.setValidator(self.double_validator)
        self.montant_initial_input.textEdited.connect(self.format_solde_input) # Réutiliser le formateur pour le montant

        self.date_debut_input = CustomDateEdit(self)
        self.date_debut_input.setCalendarPopup(True)
        self.date_debut_input.setDate(QDate.currentDate()) # Date par défaut à aujourd'hui

        self.duree_ans_input = QLineEdit(self)
        self.duree_ans_input.setValidator(self.int_validator)
        self.duree_ans_input.setPlaceholderText("Années")

        self.taux_annuel_initial_input = QLineEdit(self)
        self.taux_annuel_initial_input.setValidator(self.taux_validator)
        self.taux_annuel_initial_input.setPlaceholderText("Ex: 0.035 ou 3.5%")

        self.assurance_par_periode_input = QLineEdit(self)
        self.assurance_par_periode_input.setValidator(self.double_validator)
        self.assurance_par_periode_input.setPlaceholderText("Montant d'assurance par période")

        self.frequence_paiement_input = QComboBox(self)
        self.frequence_paiement_input.addItems(['mensuel', 'trimestriel', 'semestriel', 'annuel'])

        # Ajout des champs au formulaire
        self.form_layout.addRow(QLabel("Nom du Prêt:"), self.nom_input)
        self.form_layout.addRow(QLabel("Montant Initial du Prêt:"), self.montant_initial_input)
        self.form_layout.addRow(QLabel("Date de Début:"), self.date_debut_input)
        self.form_layout.addRow(QLabel("Durée du prêt (années):"), self.duree_ans_input)
        self.form_layout.addRow(QLabel("Taux Annuel Initial:"), self.taux_annuel_initial_input)
        self.form_layout.addRow(QLabel("Assurance par période:"), self.assurance_par_periode_input)
        self.form_layout.addRow(QLabel("Fréquence de paiement:"), self.frequence_paiement_input)

        # --- Section Taux Variables ---
        self.taux_variables_group_label = QLabel("Taux Variables (Optionnel):")
        self.form_layout.addRow(self.taux_variables_group_label)

        # Champs pour ajouter un nouveau taux variable
        self.new_taux_date_input = CustomDateEdit(self)
        self.new_taux_date_input.setCalendarPopup(True)
        self.new_taux_date_input.setDate(QDate.currentDate())
        self.new_taux_date_input.setToolTip("Date à partir de laquelle le nouveau taux s'applique.")

        self.new_taux_value_input = QLineEdit(self)
        self.new_taux_value_input.setValidator(self.taux_validator)
        self.new_taux_value_input.setPlaceholderText("Nouveau Taux Annuel (Ex: 0.04)")
        self.new_taux_value_input.setToolTip("Nouveau taux annuel (ex: 0.04 pour 4%).")

        self.add_taux_btn = QPushButton("Ajouter Taux", self)
        self.add_taux_btn.clicked.connect(self.add_taux_variable)

        taux_add_layout = QHBoxLayout()
        taux_add_layout.addWidget(QLabel("Date d'application:"))
        taux_add_layout.addWidget(self.new_taux_date_input)
        taux_add_layout.addWidget(QLabel("Nouveau Taux:"))
        taux_add_layout.addWidget(self.new_taux_value_input)
        taux_add_layout.addWidget(self.add_taux_btn)
        
        self.form_layout.addRow(taux_add_layout)

        # Tableau pour afficher les taux variables ajoutés
        self.taux_variables_table = QTableWidget(self)
        self.taux_variables_table.setColumnCount(2)
        self.taux_variables_table.setHorizontalHeaderLabels(["Date d'application", "Taux Annuel"])
        self.taux_variables_table.horizontalHeader().setStretchLastSection(True)
        self.taux_variables_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.taux_variables_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.taux_variables_table.setMinimumHeight(100) # Pour qu'il soit visible même vide

        self.remove_taux_btn = QPushButton("Supprimer Taux Sélectionné", self)
        self.remove_taux_btn.clicked.connect(self.remove_taux_variable)
        
        self.form_layout.addRow(self.taux_variables_table)
        self.form_layout.addRow(self.remove_taux_btn)


        self.main_layout.addLayout(self.form_layout)

        # Bouton de validation
        self.submit_btn = QPushButton("Valider", self)
        self.submit_btn.clicked.connect(self.submit)
        self.main_layout.addWidget(self.submit_btn)

        self.setLayout(self.main_layout)

        # Si modification, pré-remplir les champs
        if self.loan:
            self.nom_input.setText(self.loan.nom)
            self.montant_initial_input.setText(f"{self.loan.montant_initial:,.2f}".replace(",", " ").replace(".", ","))
            self.date_debut_input.setDate(QDate(self.loan.date_debut.year, self.loan.date_debut.month, self.loan.date_debut.day))
            self.duree_ans_input.setText(str(self.loan.duree_ans))
            self.taux_annuel_initial_input.setText(str(self.loan.taux_annuel_initial))
            self.assurance_par_periode_input.setText(str(self.loan.assurance_par_periode))
            index_freq = self.frequence_paiement_input.findText(self.loan.frequence_paiement)
            if index_freq != -1:
                self.frequence_paiement_input.setCurrentIndex(index_freq)
            
            # Charger les taux variables existants dans le tableau
            if self.loan.taux_variables:
                for d, t in self.loan.taux_variables:
                    self.taux_variables_data.append((d, t))
                self.update_taux_variables_table()

    def add_taux_variable(self):
        taux_date_qdate = self.new_taux_date_input.date()
        taux_date_py = date(taux_date_qdate.year(), taux_date_qdate.month(), taux_date_qdate.day())

        taux_value_str = self.new_taux_value_input.text().replace(",", ".")
        try:
            taux_value = float(taux_value_str)
            if taux_value < 0 or taux_value > 1.0:
                QMessageBox.warning(self, "Erreur", "Le taux doit être entre 0 et 1 (ex: 0.035).")
                return
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le nouveau taux doit être un nombre décimal valide.")
            return

        # Vérifier si un taux existe déjà pour cette date
        for i, (existing_date, _) in enumerate(self.taux_variables_data):
            if existing_date == taux_date_py:
                reply = QMessageBox.question(self, "Taux Existant", 
                                             f"Un taux existe déjà pour le {taux_date_py.strftime('%d/%m/%Y')}. Voulez-vous le remplacer?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.taux_variables_data[i] = (taux_date_py, taux_value)
                    self.update_taux_variables_table()
                    self.new_taux_value_input.clear()
                    return
                else:
                    return

        self.taux_variables_data.append((taux_date_py, taux_value))
        self.taux_variables_data.sort(key=lambda x: x[0]) # Trier par date
        self.update_taux_variables_table()
        self.new_taux_value_input.clear() # Effacer le champ après ajout

    def remove_taux_variable(self):
        selected_rows = self.taux_variables_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Suppression", "Veuillez sélectionner une ligne à supprimer.")
            return

        # Supprimer en partant de la fin pour éviter les problèmes d'index
        for index in sorted(selected_rows, reverse=True):
            del self.taux_variables_data[index.row()]
        self.update_taux_variables_table()

    def update_taux_variables_table(self):
        self.taux_variables_table.setRowCount(len(self.taux_variables_data))
        for row, (d, t) in enumerate(self.taux_variables_data):
            self.taux_variables_table.setItem(row, 0, QTableWidgetItem(d.strftime("%d/%m/%Y")))
            self.taux_variables_table.setItem(row, 1, QTableWidgetItem(f"{t*100:.3f}%")) # Afficher le taux en pourcentage

    def submit(self):
        nom = self.nom_input.text().strip()
        montant_initial_str = self.montant_initial_input.text().replace(" ", "").replace(",", ".")
        date_debut_qdate = self.date_debut_input.date()
        date_debut_py = date(date_debut_qdate.year(), date_debut_qdate.month(), date_debut_qdate.day())
        duree_ans_str = self.duree_ans_input.text()
        taux_annuel_initial_str = self.taux_annuel_initial_input.text().replace(",", ".")
        assurance_par_periode_str = self.assurance_par_periode_input.text().replace(",", ".")
        frequence_paiement = self.frequence_paiement_input.currentText()

        # Validations des champs obligatoires
        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom du prêt est obligatoire.")
            return
        
        try:
            montant_initial = float(montant_initial_str)
            if montant_initial <= 0:
                raise ValueError("Le montant initial doit être un nombre positif.")
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le montant initial du prêt doit être un nombre valide.")
            return

        try:
            duree_ans = int(duree_ans_str)
            if duree_ans <= 0:
                raise ValueError("La durée doit être un nombre entier positif.")
        except ValueError:
            QMessageBox.warning(self, "Erreur", "La durée du prêt doit être un nombre entier valide en années.")
            return

        try:
            taux_annuel_initial = float(taux_annuel_initial_str)
            if taux_annuel_initial < 0 or taux_annuel_initial > 1.0:
                raise ValueError("Le taux annuel initial doit être entre 0 et 1 (ex: 0.035).")
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le taux annuel initial doit être un nombre décimal valide.")
            return
        
        try:
            assurance_par_periode = float(assurance_par_periode_str)
            if assurance_par_periode < 0:
                raise ValueError("L'assurance ne peut pas être négative.")
        except ValueError:
            QMessageBox.warning(self, "Erreur", "L'assurance par période doit être un nombre décimal valide.")
            return

        # Récupérer les taux variables depuis self.taux_variables_data
        taux_variables_sorted = sorted(self.taux_variables_data, key=lambda x: x[0])


        if self.loan:
            # Modification d'un prêt existant
            self.loan.nom = nom
            self.loan.montant_initial = montant_initial
            self.loan.date_debut = date_debut_py
            self.loan.duree_ans = duree_ans
            self.loan.taux_annuel_initial = taux_annuel_initial
            self.loan.frequence_paiement = frequence_paiement
            self.loan.assurance_par_periode = assurance_par_periode
            self.loan.taux_variables = taux_variables_sorted
            
            # Appelez la méthode de mise à jour du parent (votre fenêtre principale)
            if self.parent() and hasattr(self.parent(), 'update_loan'):
                self.parent().update_loan(self.loan)
            else:
                QMessageBox.warning(self, "Erreur", "La méthode 'update_loan' n'est pas disponible dans la fenêtre parente.")
                return
        else:
            # Création d'un nouveau prêt
            new_loan = Loan(
                nom=nom,
                montant_initial=montant_initial,
                date_debut=date_debut_py,
                duree_ans=duree_ans,
                taux_annuel_initial=taux_annuel_initial,
                frequence_paiement=frequence_paiement,
                assurance_par_periode=assurance_par_periode,
                taux_variables=taux_variables_sorted
            )
            # Appelez la méthode d'ajout du parent (votre fenêtre principale)
            if self.parent() and hasattr(self.parent(), 'add_loan'):
                self.parent().add_loan(new_loan)
            else:
                QMessageBox.warning(self, "Erreur", "La méthode 'add_loan' n'est pas disponible dans la fenêtre parente.")
                return

        self.accept()

    def format_solde_input(self):
        # Cette fonction est réutilisée pour le montant initial du prêt
        text = self.montant_initial_input.text()
        clean_text = ''.join(c for c in text if c.isdigit() or c in [',', '.'])
        clean_text = clean_text.replace(",", ".")

        if '.' in clean_text:
            partie_entiere, partie_decimale = clean_text.split('.', 1)
            if partie_entiere:
                partie_entiere = "{:,}".format(int(partie_entiere)).replace(",", " ")
            else:
                partie_entiere = "0"
            formatted = partie_entiere + ',' + partie_decimale
        else:
            if clean_text:
                formatted = "{:,}".format(int(clean_text)).replace(",", " ")
            else:
                formatted = ""

        self.montant_initial_input.blockSignals(True)
        self.montant_initial_input.setText(formatted)
        self.montant_initial_input.blockSignals(False)
        # Maintenir le curseur à la bonne position (facultatif mais améliore l'UX)
        cursor_pos = len(formatted)
        if '.' in clean_text and '.' in text:
            original_dot_index = text.find('.')
            formatted_dot_index = formatted.find(',')
            if original_dot_index != -1 and formatted_dot_index != -1:
                cursor_pos = formatted_dot_index + (text.find('.') - original_dot_index)
        self.montant_initial_input.setCursorPosition(cursor_pos)