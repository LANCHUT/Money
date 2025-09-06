from PyQt6.QtWidgets import (
    QPushButton, QLabel, QDialog, QLineEdit, QFormLayout,
    QMessageBox, QComboBox, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QHeaderView, QAbstractItemView
)
from utils.DateTableWidgetItem import CustomDateEdit
from PyQt6.QtCore import Qt, QDate, QLocale
from PyQt6.QtGui import QDoubleValidator, QIntValidator

from views.dialogs.BaseDialog import BaseDialog
from models import Loan
from datetime import date
from database.gestion_bd import GetComptesHorsPlacement,GetCompteName


class AddEditLoanDialog(BaseDialog):
    def __init__(self, parent=None, loan: Loan = None,current_account = None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier un Prêt")
        self.setMinimumWidth(500)

        self.loan = loan
        self.current_account = current_account
        self.taux_variables_data = []

        # Valideurs pour les champs numériques
        self.int_validator = QIntValidator(1, 1000, self)
        
        # --- Utilisation d'une locale pour le point décimal ---
        # La locale "en_US" utilise naturellement le point.
        locale_dot_decimal = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
        
        # On peut configurer le nombre de décimales directement ici
        self.double_validator = QDoubleValidator(0.0, 999999999.0, 2, self)
        self.double_validator.setLocale(locale_dot_decimal)
        
        self.taux_validator = QDoubleValidator(0.0, 100.0, 5, self)
        self.taux_validator.setLocale(locale_dot_decimal)

        # Layout principal
        self.main_layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        # --- Champs communs du prêt ---
        self.nom_input = QLineEdit(self)
        self.montant_initial_input = QLineEdit(self)
        # Le validateur QDoubleValidator gère maintenant la saisie.
        # On va juste connecter la mise à jour pour le formatage visuel.
        self.montant_initial_input.setValidator(self.double_validator)
        self.montant_initial_input.textChanged.connect(self.format_montant_input)

        self.date_debut_input = CustomDateEdit(self)
        self.date_debut_input.setCalendarPopup(True)
        self.date_debut_input.setDate(QDate.currentDate())

        self.duree_ans_input = QLineEdit(self)
        self.duree_ans_input.setValidator(self.int_validator)
        self.duree_ans_input.setPlaceholderText("Années")

        self.taux_annuel_initial_input = QLineEdit(self)
        self.taux_annuel_initial_input.setValidator(self.taux_validator)
        self.taux_annuel_initial_input.setPlaceholderText("Ex: 3.5 pour 3.5%")

        self.assurance_par_periode_input = QLineEdit(self)
        self.assurance_par_periode_input.setValidator(self.double_validator)
        self.assurance_par_periode_input.setPlaceholderText("Montant d'assurance par période")

        self.compte_associe_input = QComboBox(self)
        comptes_courant = GetComptesHorsPlacement()
        for compte in comptes_courant:
            if compte.type == "Courant":
                self.compte_associe_input.addItem(str(compte.nom),userData=str(compte._id))

        self.frequence_paiement_input = QComboBox(self)
        self.frequence_paiement_input.addItems(['Mensuelle', 'Trimestrielle', 'Semestrielle', 'Annuelle'])

        # Ajout des champs au formulaire
        self.form_layout.addRow(QLabel("Nom du Prêt:"), self.nom_input)
        self.form_layout.addRow(QLabel("Montant Initial du Prêt:"), self.montant_initial_input)
        self.form_layout.addRow(QLabel("Date de Début:"), self.date_debut_input)
        self.form_layout.addRow(QLabel("Durée du prêt (années):"), self.duree_ans_input)
        self.form_layout.addRow(QLabel("Taux Annuel Initial (%):"), self.taux_annuel_initial_input)
        self.form_layout.addRow(QLabel("Assurance par période:"), self.assurance_par_periode_input)
        self.form_layout.addRow(QLabel("Fréquence de paiement:"), self.frequence_paiement_input)
        self.form_layout.addRow(QLabel("Compte associé"),self.compte_associe_input)

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
        self.new_taux_value_input.setPlaceholderText("Nouveau Taux Annuel (Ex: 4 pour 4%)")
        self.new_taux_value_input.setToolTip("Nouveau taux annuel en pourcentage (ex: 4 pour 4%).")

        self.add_taux_btn = QPushButton("Ajouter Taux", self)
        self.add_taux_btn.clicked.connect(self.add_taux_variable)

        taux_add_layout = QHBoxLayout()
        taux_add_layout.addWidget(QLabel("Date d'application:"))
        taux_add_layout.addWidget(self.new_taux_date_input)
        taux_add_layout.addWidget(QLabel("Nouveau Taux (%):"))
        taux_add_layout.addWidget(self.new_taux_value_input)
        taux_add_layout.addWidget(self.add_taux_btn)
        
        self.form_layout.addRow(taux_add_layout)

        # Tableau pour afficher les taux variables ajoutés
        self.taux_variables_table = QTableWidget(self)
        self.taux_variables_table.setColumnCount(2)
        self.taux_variables_table.setHorizontalHeaderLabels(["Date d'application", "Taux Annuel (%)"])
        self.taux_variables_table.horizontalHeader().setStretchLastSection(True)
        self.taux_variables_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.taux_variables_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.taux_variables_table.setMinimumHeight(100)

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
            # Remplacer le point par la virgule pour l'affichage initial
            self.montant_initial_input.setText(f"{self.loan.montant_initial:,.2f}".replace(",", " ").replace(".", ","))
            self.date_debut_input.setDate(QDate(self.loan.date_debut.year, self.loan.date_debut.month, self.loan.date_debut.day))
            self.duree_ans_input.setText(str(int(self.loan.duree_ans)))
            self.taux_annuel_initial_input.setText(f"{self.loan.taux_annuel_initial * 100:.3f}".replace(".", ","))
            self.assurance_par_periode_input.setText(f"{self.loan.assurance_par_periode:.2f}".replace(".", ","))
            self.compte_associe_input.setCurrentText(GetCompteName(self.loan.compte_associe))
            index_freq = self.frequence_paiement_input.findText(self.loan.frequence_paiement)
            if index_freq != -1:
                self.frequence_paiement_input.setCurrentIndex(index_freq)
            
            # Charger les taux variables existants dans le tableau
            if self.loan.taux_variables:
                self.taux_variables_data = list(self.loan.taux_variables)
                self.update_taux_variables_table()

    def format_montant_input(self):
        # Sauvegarder la position du curseur
        cursor_pos = self.montant_initial_input.cursorPosition()
        current_text = self.montant_initial_input.text()
        
        # Nettoyer le texte pour le traitement : enlever les espaces et remplacer la virgule par un point
        clean_text = current_text.replace(" ", "").replace(",", ".")
        
        # Vérifier si le texte nettoyé est un nombre valide
        try:
            val = float(clean_text)
            
            # Formater la partie entière avec des espaces pour les milliers
            if '.' in clean_text:
                entier, decimal = clean_text.split('.', 1)
                formatted_entier = "{:,}".format(int(entier)).replace(",", " ")
                formatted_text = formatted_entier + ',' + decimal
            else:
                formatted_text = "{:,}".format(int(clean_text)).replace(",", " ")
            
            # Bloquer les signaux pour éviter une boucle de re-formatage
            self.montant_initial_input.blockSignals(True)
            
            # Calculer la nouvelle position du curseur
            # On se base sur le nombre de caractères non-espaces avant le curseur
            original_prefix_len = len(current_text[:cursor_pos].replace(" ", ""))
            new_cursor_pos = 0
            count = 0
            for char in formatted_text:
                if count == original_prefix_len:
                    break
                if char != " ":
                    count += 1
                new_cursor_pos += 1
            
            self.montant_initial_input.setText(formatted_text)
            self.montant_initial_input.setCursorPosition(new_cursor_pos)
            
            self.montant_initial_input.blockSignals(False)

        except ValueError:
            # Si le texte n'est pas un nombre valide, ne rien faire
            pass
            
    # Les autres méthodes (add_taux_variable, remove_taux_variable, submit, etc.) restent les mêmes
    def add_taux_variable(self):
        taux_date_qdate = self.new_taux_date_input.date()
        taux_date_py = date(taux_date_qdate.year(), taux_date_qdate.month(), taux_date_qdate.day())

        taux_value_str = self.new_taux_value_input.text().replace(",", ".")
        try:
            taux_value_percent = float(taux_value_str)
            taux_value = taux_value_percent / 100.0
            if taux_value < 0 or taux_value > 1.0:
                QMessageBox.warning(self, "Erreur", "Le taux doit être entre 0% et 100%.")
                return
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le nouveau taux doit être un nombre valide (ex: 3.5).")
            return

        for i, (existing_date, _) in enumerate(self.taux_variables_data):
            if existing_date == taux_date_py:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Taux Existant")
                msg_box.setText(f"Un taux existe déjà pour le {taux_date_py.strftime('%d/%m/%Y')}. Voulez-vous le remplacer ?")
                
                bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
                bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
                
                msg_box.setIcon(QMessageBox.Icon.Question)
                msg_box.exec()
                
                if msg_box.clickedButton() == bouton_oui:
                    self.taux_variables_data[i] = (taux_date_py, taux_value)
                    self.update_taux_variables_table()
                    self.new_taux_value_input.clear()
                    return
                else:
                    return

        self.taux_variables_data.append((taux_date_py, taux_value))
        self.taux_variables_data.sort(key=lambda x: x[0])
        self.update_taux_variables_table()
        self.new_taux_value_input.clear()

    def remove_taux_variable(self):
        selected_rows = self.taux_variables_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Suppression", "Veuillez sélectionner une ligne à supprimer.")
            return

        for index in sorted(selected_rows, reverse=True):
            del self.taux_variables_data[index.row()]
        self.update_taux_variables_table()

    def update_taux_variables_table(self):
        self.taux_variables_table.setRowCount(len(self.taux_variables_data))
        for row, (d, t) in enumerate(self.taux_variables_data):
            self.taux_variables_table.setItem(row, 0, QTableWidgetItem(d.strftime("%d/%m/%Y")))
            self.taux_variables_table.setItem(row, 1, QTableWidgetItem(f"{t*100:.3f}%".replace(".", ",")))

    def submit(self):
        nom = self.nom_input.text().strip()
        montant_initial_str = self.montant_initial_input.text().replace(" ", "").replace(",", ".")
        date_debut_qdate = self.date_debut_input.date()
        date_debut_py = date(date_debut_qdate.year(), date_debut_qdate.month(), date_debut_qdate.day())
        duree_ans_str = self.duree_ans_input.text()
        compte_associe = self.compte_associe_input.currentData(Qt.ItemDataRole.UserRole)
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
            taux_annuel_initial_percent = float(taux_annuel_initial_str)
            taux_annuel_initial = taux_annuel_initial_percent / 100.0
            if taux_annuel_initial < 0 or taux_annuel_initial > 1.0:
                raise ValueError("Le taux annuel initial doit être entre 0% et 100%.")
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Le taux annuel initial doit être un nombre valide (ex: 3.5).")
            return
        
        try:
            assurance_par_periode = float(assurance_par_periode_str)
            if assurance_par_periode < 0:
                raise ValueError("L'assurance ne peut pas être négative.")
        except ValueError:
            QMessageBox.warning(self, "Erreur", "L'assurance par période doit être un nombre valide.")
            return

        taux_variables_sorted = sorted(self.taux_variables_data, key=lambda x: x[0])

        if self.loan:
            self.loan.nom = nom
            self.loan.montant_initial = montant_initial
            self.loan.date_debut = date_debut_py
            self.loan.duree_ans = duree_ans
            self.loan.taux_annuel_initial = taux_annuel_initial
            self.loan.frequence_paiement = frequence_paiement
            self.loan.assurance_par_periode = assurance_par_periode
            self.loan.taux_variables = taux_variables_sorted
            self.loan.compte_associe = compte_associe
            
            if self.parent():
                self.parent().update_loan(self.loan)
        else:
            new_loan = Loan(
                nom=nom,
                montant_initial=montant_initial,
                date_debut=date_debut_py,
                duree_ans=duree_ans,
                taux_annuel_initial=taux_annuel_initial,
                frequence_paiement=frequence_paiement,
                assurance_par_periode=assurance_par_periode,
                taux_variables=taux_variables_sorted,
                compte_id=self.current_account,
                compte_associe=compte_associe
            )

            self.parent().add_loan(new_loan)

        self.accept()