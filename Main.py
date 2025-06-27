import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QListWidgetItem, QMessageBox,
    QAbstractItemView, QTabWidget,QMenu,QStackedLayout,QGridLayout,QSpacerItem,QSizePolicy
)
from ShowPointageDialog import show_pointage_dialog, handle_bq_click, finalize_pointage,cancel_pointage
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QAction,QColor
from PyQt6.QtCore import Qt,QPoint,QUrl
from GestionBD import *
from CheckableComboBox import *
from DateTableWidgetItem import *
from AddEditAccountDialog import *
from AddEditOperationDialog import *
from AddEditTypeBeneficiaireDialog import *
from AddEditBeneficiaireDialog import *
from AddPositionDialog import *
from AddEditTierDialog import *
from AddEditPlacementDialog import *
from ReplaceTierDialog import *
from ReplaceSousCategorieDialog import *
from ReplaceCategorieDialog import *
from ReplaceTypeTierDialog import *
from ReplaceMoyenPaiementDialog import *
from AddEditSousCategorieDialog import *
from AddEditCategorieDialog import *
from AddEditTypeTierDialog import *
from AddEditMoyenPaiementDialog import *
from ShowPerformanceDialog import *
from typing import Optional
from PyQt6.QtWebEngineWidgets import QWebEngineView
from Datas import TypeOperation
import plotly.graph_objects as go
import plotly.graph_objs as go
import json
import plotly
import os
from datetime import datetime


def align_center(item: QTableWidgetItem) -> QTableWidgetItem:
    item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
    return item

def format_montant(montant):
    return f"{float(montant):,.2f}".replace(",", " ").replace(".", ",") + " €" if montant != 0 else ""

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, text):
        super().__init__(text)
        self.value = value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)
    
class MoneyManager(QMainWindow):
    def __init__(self):
        super().__init__()
        create_tables()  # Mieux ici qu'en dehors
        self.current_account = None
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.pointage_state = {'actif': False, 'solde': 0.0, 'date': '','ops' : set(),'rows' : set(),'suspendu': False}

        self.setWindowTitle("Money Manager")

        self.setup_ui()
        self.showFullScreen()

    def setup_ui(self):
        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Fichier")
        help_menu = menu_bar.addMenu("Aide")

        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # --- Onglet Accueil ---
        self.accueil_tab = QWidget()
        self.tabs.addTab(self.accueil_tab, "Accueil")
        self.setup_accueil_tab()

        # --- Onglet Opération ---
        self.operation_tab = QWidget()
        self.tabs.addTab(self.operation_tab, "Gestion des opérations")
        self.setup_operation_tab()

        # --- Onglet Tier ---
        self.tier_tab = QWidget()
        self.tabs.addTab(self.tier_tab, "Gestion des tiers")
        self.setup_tiers_tab()

        # --- Onglet Placement ---
        self.placement_tab = QWidget()
        self.tabs.addTab(self.placement_tab, "Gestion des placements")
        self.setup_placement_tab()

        self.comptes_tab = QWidget()
        self.tabs.addTab(self.comptes_tab, "Gestion des comptes")
        self.setup_comptes_tab()

        self.categories_tab = QWidget()
        self.tabs.addTab(self.categories_tab, "Gestion des catégories")
        self.setup_categories_tab()

        self.categories2_tab = QWidget()
        self.tabs.addTab(self.categories2_tab, "Gestion des Bénéficiaires")
        self.setup_categories2_tab()

        self.echeancier_tab = QWidget()
        self.tabs.addTab(self.echeancier_tab, "Gestion de l'échéancier")
        self.setup_echeancier_tab()

    def setup_echeancier_tab(self):
        layout = QVBoxLayout(self.echeancier_tab)

        self.echeance_table = QTableWidget(0, 19)
        self.echeance_table.setHorizontalHeaderLabels(["Fréquence", "1 ère\néchéance", "Prochaine\néchéance", "Compte", "Type\nopération", "Compte\nassocié", "Type\nde\ntiers", "Tiers\nPlacement",
                                                       "Catégorie","Sous-\nCatégorie","Type\nbénéficiaire","Bénéficiaire","Débit","Crédit","Nb parts","Val part","Frais","Intérêts","Notes"])
        self.echeance_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.echeance_table.setAlternatingRowColors(True)
        self.echeance_table.setSortingEnabled(True)

        generer_btn = QPushButton("Générer opérations")
        # generer_btn.clicked.connect(self.generer_operations_echeances)

        layout.addWidget(self.echeance_table)
        layout.addWidget(generer_btn)

    def load_accounts(self):
        for compte in GetComptes():
            self.add_account_to_list(compte)
        self.add_total_to_list()  # Ajoute le total à la fin

    def load_tiers(self):
        self.tier_table.setSortingEnabled(False)
        self.tier_table.setRowCount(0)

        tiers = GetTiers()
        self.tier_table.setRowCount(len(tiers))

        for row, tier in enumerate(tiers):
            self.add_tier_row(row, tier)

        self.tier_table.resizeColumnsToContents()
        self.tier_table.setSortingEnabled(True)

    def load_position(self):
        self.position_table.setRowCount(0)
        for position in GetPositions(self.current_account):
            self.add_position_row(position)
            
    def load_sous_categories(self):
        self.sous_categorie_table.setSortingEnabled(False)
        sous_categories = GetAllSousCategorie()
        self.sous_categorie_table.setRowCount(len(sous_categories))
        
        for row, sous_cat in enumerate(sous_categories):
            self.add_sous_categorie_row(row, sous_cat)

        self.sous_categorie_table.resizeColumnsToContents()
        self.sous_categorie_table.setSortingEnabled(True)

    def load_beneficiaire(self):
        self.sous_categorie2_table.setSortingEnabled(False)
        beneficiaires = GetAllBeneficiaire()
        self.sous_categorie2_table.setRowCount(len(beneficiaires))
        
        for row, beneficiaire in enumerate(beneficiaires):
            self.add_beneficiaire_row(row, beneficiaire)

        self.sous_categorie2_table.resizeColumnsToContents()
        self.sous_categorie2_table.setSortingEnabled(True)

    def load_placement(self):
        self.placement_table.setSortingEnabled(False)
        placements = GetLastPlacement()
        self.placement_table.setRowCount(len(placements))

        for row, placement in enumerate(placements):
            self.add_placement_row(row, placement)

        self.placement_table.resizeColumnsToContents()
        self.placement_table.setSortingEnabled(True)

    def load_categorie(self):
        self.categorie_table.setSortingEnabled(False)
        categories = GetCategorie()
        self.categorie_table.setRowCount(len(categories))

        for row, cat in enumerate(categories):
            self.add_categorie_row(row, cat)

        self.categorie_table.resizeColumnsToContents()
        self.categorie_table.setSortingEnabled(True)

    def load_type_beneficiaire(self):
        self.categorie2_table.setSortingEnabled(False)
        types_beneficiaire = GetTypeBeneficiaire()
        self.categorie2_table.setRowCount(len(types_beneficiaire))

        for row, type in enumerate(types_beneficiaire):
            self.add_type_beneficiaire_row(row, type)

        self.categorie2_table.resizeColumnsToContents()
        self.categorie2_table.setSortingEnabled(True)

    def load_moyen_paiement(self):
        self.moyen_paiement_table.setSortingEnabled(False)
        moyens = GetMoyenPaiement()
        self.moyen_paiement_table.setRowCount(len(moyens))

        for row, mp in enumerate(moyens):
            self.add_moyen_paiement_row(row, mp)

        self.moyen_paiement_table.resizeColumnsToContents()
        self.moyen_paiement_table.setSortingEnabled(True)

    def load_type_tier(self):
        self.type_tier_table.setSortingEnabled(False)
        types = GetTypeTier()
        self.type_tier_table.setRowCount(len(types))

        for row, tt in enumerate(types):
            self.add_type_tier_row(row, tt)

        self.type_tier_table.resizeColumnsToContents()
        self.type_tier_table.setSortingEnabled(True)

    def load_comptes(self):
        self.compte_table.setSortingEnabled(False)
        comptes = GetComptes()
        self.compte_table.setRowCount(len(comptes))

        for row, compte in enumerate(comptes):
            self.add_compte_row(row, compte)

        self.compte_table.resizeColumnsToContents()
        self.compte_table.setSortingEnabled(True)

    def add_account_to_list(self, compte):
        # Création du widget de ligne
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setColumnStretch(0, 3)  # nom
        layout.setColumnStretch(1, 1)  # type
        layout.setColumnStretch(2, 2)  # solde

        # Nom du compte
        name_label = QLabel(compte.nom)
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Type de compte
        type_label = QLabel(compte.type)
        type_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Solde formaté
        solde_str = f"{compte.solde:,.2f}".replace(",", " ").replace(".", ",") + " €"
        solde_label = QLabel(solde_str)
        solde_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Ajout des widgets au layout
        layout.addWidget(name_label, 0, 0)
        layout.addWidget(type_label, 0, 1)
        layout.addWidget(solde_label, 0, 2)

        # Création de l'item dans la QListWidget
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, {"id": compte._id, "nom": compte.nom})
        item.setSizeHint(widget.sizeHint())
        
        self.account_list.addItem(item)
        self.account_list.setItemWidget(item, widget)

    def on_account_clicked(self, item):
        try:
            self.current_account = str(item.data(Qt.ItemDataRole.UserRole)["id"])
            selected_account = GetCompte(self.current_account)
            self.tabs.setCurrentWidget(self.operation_tab)
            self.reset_filters()
            self.compte_filter.set_all_checked(False)
            self.compte_filter.checkItemByText(selected_account.nom)
            if not selected_account:
                return

            if selected_account.type == "Placement":
                self.table_stack.setCurrentIndex(1)  # Affiche position_table
                self.add_transaction_btn.setText("Ajouter une position")
                self.add_transaction_btn.clicked.disconnect()
                self.add_transaction_btn.clicked.connect(self.open_add_position_dialog)
                self.show_performance_btn.show()
                self.pointage_btn.hide()

                self.position_table.setRowCount(0)
                for placement in GetPositions(str(self.current_account)):
                    self.add_position_row(placement)
            else:
                self.table_stack.setCurrentIndex(0)  # Affiche transaction_table
                self.add_transaction_btn.setText("Ajouter une opération")
                self.add_transaction_btn.clicked.disconnect()
                self.add_transaction_btn.clicked.connect(self.open_add_operation_dialog)
                self.show_performance_btn.hide()
                self.pointage_btn.show()
                self.load_operations()

        except Exception as e:
            print("Erreur:", e)
            QMessageBox.warning(self, "Attention", "Le compte 'Total' n'est pas un compte valide, Veuillez choisir un autre compte.")
        

    def open_add_account_dialog(self):
        dialog = AddEditAccountDialog(self)
        dialog.exec()

    def open_add_tier_dialog(self):
        dialog = AddEditTierDialog(self)
        dialog.exec()

    def open_add_beneficiaire_dialog(self):
        dialog = AddEditBeneficiaireDialog(self)
        dialog.exec()

    def open_add_sous_categorie_dialog(self):
        dialog = AddEditSousCategorieDialog(self)
        dialog.exec()
    def open_add_categorie_dialog(self):
        dialog = AddEditCategorieDialog(self)
        dialog.exec()

    def open_add_type_beneficiaire_dialog(self):
        dialog = AddEditTypeBeneficiaireDialog(self)
        dialog.exec()

    def open_add_type_tier_dialog(self):
        dialog = AddEditTypeTierDialog(self)
        dialog.exec()
    def open_add_moyen_paiement_dialog(self):
        dialog = AddEditMoyenPaiementDialog(self)
        dialog.exec()

    def open_add_placement_dialog(self):
        dialog = AddEditPlacementDialog(self)
        dialog.exec()

    def edit_selected_tier(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.tier_table.item(row, 0)
        nom = item_nom.text()
        tier_id = item_nom.data(Qt.ItemDataRole.UserRole)  # <<< Récupération de l'ID
        type_tier = self.tier_table.item(row, 1).text()
        cat_def = self.tier_table.item(row, 2).text()
        sous_cat_defaut = self.tier_table.item(row, 3).text()
        moy_paiement_defaut = self.tier_table.item(row, 4).text()
        actif = self.tier_table.item(row,5).text()

        # Créer l'objet Tier existant
        tier = Tier(nom, type_tier, cat_def, sous_cat_defaut, moy_paiement_defaut, tier_id, actif)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditTierDialog(self, tier=tier)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.tier_table.item(row, 0).setText(dialog.nom.text())
            self.tier_table.item(row, 1).setText(dialog.type_tier.currentText())
            self.tier_table.item(row, 2).setText(dialog.cat_def.currentText())
            self.tier_table.item(row, 3).setText(dialog.sous_cat_defaut.currentText())
            self.tier_table.item(row, 4).setText(dialog.moy_paiement_defaut.currentText())
            etat = "Actif" if dialog.actif.checkState().value else "Inactif"
            self.tier_table.item(row, 5).setText(etat)
            
            # Mettre à jour l'ID si besoin (normalement pas nécessaire sauf si recréation)
            self.tier_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, tier_id)

    def edit_selected_placement(self, row):
        # Récupérer uniquement les informations nécessaires
        nom = self.placement_table.item(row, 0).text()
        type = self.placement_table.item(row, 1).text()
        date = self.placement_table.item(row, 2).text()
        valeur_actualise = self.placement_table.item(row, 3).text()
        origine = self.placement_table.item(row, 4).text()

        # Créer un objet Placement existant
        placement = HistoriquePlacement(nom, type,date,valeur_actualise,origine)

        # Ouvrir la boîte de dialogue en mode modification (seul le nom sera modifiable)
        dialog = AddEditPlacementDialog(self, placement=placement)
        if dialog.exec():
            # Mettre à jour uniquement la colonne du nom dans le tableau
            self.placement_table.item(row, 0).setText(dialog.nom.text())

    def actualiser_selected_placement(self, row):
        # Récupérer les infos du placement existant
        nom = self.placement_table.item(row, 0).text()
        type = self.placement_table.item(row, 1).text()
        date = self.placement_table.item(row, 2).text()
        valeur_actualise = self.placement_table.item(row, 3).text()
        origine = self.placement_table.item(row, 4).text()

        placement = HistoriquePlacement(nom, type, date, valeur_actualise, origine)

        dialog = AddEditPlacementDialog(self, placement=placement, mode="actualiser")
        if dialog.exec():
            # Mise à jour complète de la ligne existante
            self.placement_table.item(row, 0).setText(dialog.nom.text())
            self.placement_table.item(row, 1).setText(dialog.type.currentText())
            self.placement_table.item(row, 2).setText(dialog.date.date().toString("dd/MM/yyyy"))
            self.placement_table.item(row, 3).setText(format_montant(float(dialog.val_actualisee.text().replace(' ',''))))
            self.placement_table.item(row, 4).setText("Actualisation")
            self.show_placement_history_graph(self.placement_table.item(row, 0))

    def edit_selected_compte(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.compte_table.item(row, 0)
        nom = item_nom.text()
        compte_id = item_nom.data(Qt.ItemDataRole.UserRole)  # <<< Récupération de l'ID
        item = self.compte_table.item(row, 1)
        if item:
            solde_str = item.text().replace(" ", "").replace(",", ".").replace("+","").replace("-","").replace("€","")  # Nettoyage
            try:
                solde = float(solde_str)
            except ValueError:
                solde = 0.0  # ou gérer l'erreur autrement
        type = self.compte_table.item(row, 2).text()
        nom_banque = self.compte_table.item(row, 3).text()
        # Créer l'objet Tier existant
        compte = Compte(nom,solde,type,nom_banque,compte_id)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditAccountDialog(self, compte=compte)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.compte_table.item(row, 0).setText(dialog.nom_input.text())
            self.compte_table.item(row, 2).setText(dialog.type_input.currentText())
            self.compte_table.item(row, 3).setText(dialog.banque_input.text())
            
            # Mettre à jour l'ID si besoin (normalement pas nécessaire sauf si recréation)
            self.compte_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, compte_id)
            

    def delete_selected_tier(self, row):
        item_nom = self.tier_table.item(row, 0)
        tier_id = str(item_nom.data(Qt.ItemDataRole.UserRole))
        nb_operations_related = GetTierRelatedOperations(tier_id)
        tier = GetTierById(tier_id)
        type_tier = tier.type

        # 🛑 Étape de confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer le tier '{tier.nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            autres_tiers = GetTiersActifByTypeExceptCurrent(type_tier, tier_id)
            if not autres_tiers:
                QMessageBox.warning(
                    self,
                    "Suppression impossible",
                    f"Aucun autre tier de type '{type_tier}' disponible pour le remplacement."
                )
                return

            dialog = ReplaceTierPopup(autres_tiers, self)
            if dialog.exec():
                nouveau_tier_id = dialog.get_selected_tier_id()
                UpdateTierInOperations(tier_id, nouveau_tier_id)
            else:
                return  # L'utilisateur a annulé

        DeleteTier(tier_id)
        self.tier_table.removeRow(row)


    def delete_selected_compte(self, row):
        choix = QMessageBox.question(
                    self,
                    "Suppression d'un compte",
                    "Toutes les opérations liés à ce compte vont être supprimées\nEtes-vous sûr de vouloir supprimer le compte ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
        if choix == QMessageBox.StandardButton.Yes:
            item_nom = self.compte_table.item(row, 0)
            compte_id = str(item_nom.data(Qt.ItemDataRole.UserRole))
            DeleteCompte(compte_id)
            self.compte_table.removeRow(row)
            self.account_list.clear()
            self.transaction_table.clear()
            self.load_accounts()

    def delete_selected_operation(self, row):
        choix = QMessageBox.question(
                    self,
                    "Suppression d'une opération",
                    "L'opération va être définitivement supprimée\nEtes-vous sûr de vouloir supprimer l'opération ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
        if choix == QMessageBox.StandardButton.Yes:
            item_nom = self.transaction_table.item(row, 0)
            operation_id = str(item_nom.data(Qt.ItemDataRole.UserRole))
            operation = GetOperation(operation_id)
            DeleteOperation(operation,operation.credit,operation.debit)
            self.transaction_table.removeRow(row)
            self.account_list.clear()
            self.transaction_table.clearContents()
            self.load_accounts()
            self.load_operations()

    def delete_selected_placement(self, row):
        choix = QMessageBox.question(
                    self,
                    "Suppression du placement",
                    "Toutes les positions liés à ce placement vont être supprimées\nEtes-vous sûr de vouloir supprimer le placement ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
        if choix == QMessageBox.StandardButton.Yes:
            nom = self.placement_table.item(row, 0).text()
            DeletePlacement(nom)
            self.placement_table.removeRow(row)
            self.account_list.clear()
            self.position_table.clearContents()
            self.compte_table.clearContents()
            self.load_accounts()
            self.load_position()
            self.load_comptes()

    def delete_selected_type_beneficiaire(self, row):
        item_nom = self.categorie2_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole))
        nb_operations_related = GetTypeBeneficiaireRelatedOperations(nom)

        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer le type de bénéficiaire '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            choix = QMessageBox.question(
                self,
                "Suppression du type de bénéficiaire",
                f"{nb_operations_related} opération(s) utilisent ce type.\n"
                "Elles seront remplacées par une valeur vide.\n"
                "Voulez-vous continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if choix != QMessageBox.StandardButton.Yes:
                return  # L'utilisateur a annulé

            UpdateTypeBeneficiaireInOperations(nom, "")  # Remplace par chaîne vide

        DeleteTypeBeneficiaire(nom)  # Supprime le type de bénéficiaire
        self.load_type_beneficiaire()
        self.load_operations()


    def delete_selected_beneficiaire(self, row):
        item_nom = self.sous_categorie2_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole))
        nb_operations_related = GetBeneficiaireRelatedOperations(nom)

        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer le bénéficiaire '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            choix = QMessageBox.question(
                self,
                "Suppression du bénéficiaire",
                f"{nb_operations_related} opération(s) utilisent ce bénéficiaire.\n"
                "Elles seront remplacées par une valeur vide.\n"
                "Voulez-vous continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if choix != QMessageBox.StandardButton.Yes:
                return  # L'utilisateur a annulé

            UpdateBeneficiaireInOperations(nom, "")  # Remplace par chaîne vide

        DeleteBeneficiaire(nom)  # Supprime le type de bénéficiaire
        self.load_beneficiaire()
        self.load_operations()
        


    def delete_selected_sous_categorie(self, row):
        item_nom = self.sous_categorie_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole)["nom"])
        categorie_parent = str(item_nom.data(Qt.ItemDataRole.UserRole)["categorie_parent"])
        nb_operations_related = GetSousCategorieRelatedOperations(nom)

        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer la sous catégorie '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_sous_categorie = GetSousCategorieByCategorieParentExceptCurrent(nom, categorie_parent)

            if not autres_sous_categorie:
                # Aucun autre sous-catégorie dispo
                choix = QMessageBox.question(
                    self,
                    "Suppression sous-catégorie",
                    "Aucune autre sous-catégorie disponible.\nVoulez-vous remplacer par une valeur vide ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if choix == QMessageBox.StandardButton.Yes:
                    DeleteSousCategorie(nom)
                    self.load_tiers()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé
            else:
                # Il y a d'autres sous-catégories disponibles
                dialog = ReplaceSousCategoriePopup(autres_sous_categorie, self)
                if dialog.exec():
                    selected_value = dialog.get_selected_sous_categorie()
                    UpdateSousCategorieInOperations(nom, selected_value)
                    UpdateSousCategorieTier(nom,selected_value)
                    self.load_tiers()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé

        # Suppression de la sous-catégorie
        DeleteSousCategorie(nom)
        self.load_tiers()
        self.load_operations()
        self.sous_categorie_table.removeRow(row)


    def delete_selected_categorie(self, row):
        item_nom = self.categorie_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole))
        nb_operations_related = GetCategorieRelatedOperations(nom)

        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer la catégorie '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_categorie = GetCategorieExceptCurrent(nom)

            if not autres_categorie:
                # Aucun autre sous-catégorie dispo
                choix = QMessageBox.question(
                    self,
                    "Suppression catégorie",
                    "Aucune autre catégorie disponible.\nVoulez-vous remplacer par une valeur vide ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if choix == QMessageBox.StandardButton.Yes:
                    DeleteCategorie(nom)
                    self.load_tiers()
                    self.load_sous_categories()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé
            else:
                # Il y a d'autres sous-catégories disponibles
                dialog = ReplaceCategoriePopup(autres_categorie, self)
                if dialog.exec():
                    selected_value = dialog.get_selected_categorie()
                    UpdateCategorieInOperations(nom, selected_value)
                    UpdateCategorieTier(nom,selected_value)
                    self.load_tiers()
                    self.load_sous_categories()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé

        # Suppression de la sous-catégorie
        DeleteCategorie(nom)
        self.load_tiers()
        self.load_operations()
        self.load_sous_categories()
        self.categorie_table.removeRow(row)

    def delete_selected_type_tier(self, row):
        item_nom = self.type_tier_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole))
        nb_operations_related = GetTypeTierRelatedOperations(nom)

        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer le type de tier '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_type_tier = GetTypeTierExceptCurrent(nom)

            if not autres_type_tier:
                # Aucun autre sous-catégorie dispo
                choix = QMessageBox.question(
                    self,
                    "Suppression type tier",
                    "Aucun autre type de tier disponible.\nVoulez-vous remplacer par une valeur vide ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if choix == QMessageBox.StandardButton.Yes:
                    DeleteTypeTier(nom)
                    self.load_tiers()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé
            else:
                # Il y a d'autres sous-catégories disponibles
                dialog = ReplaceTypeTierPopup(autres_type_tier, self)
                if dialog.exec():
                    selected_value = dialog.get_selected_type_tier()
                    UpdateTypeTierInOperations(nom, selected_value)
                    UpdateTypeTier(nom,selected_value)
                    self.load_tiers()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé

        # Suppression de la sous-catégorie
        DeleteTypeTier(nom)
        self.load_tiers()
        self.load_operations()
        self.type_tier_table.removeRow(row)


    def delete_selected_moyen_paiement(self, row):
        item_nom = self.moyen_paiement_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole))
        nb_operations_related = GetMoyenPaiementRelatedOperations(nom)

        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer le moyen de paiement '{nom}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_moyen_paiement = GetMoyenPaiementExceptCurrent(nom)

            if not autres_moyen_paiement:
                # Aucun autre sous-catégorie dispo
                choix = QMessageBox.question(
                    self,
                    "Suppression moyen de paiement",
                    "Aucun autre moyen de paiement disponible.\nVoulez-vous remplacer par une valeur vide ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if choix == QMessageBox.StandardButton.Yes:
                    DeleteMoyenPaiement(nom)
                    self.load_tiers()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé
            else:
                # Il y a d'autres sous-catégories disponibles
                dialog = ReplaceMoyenPaiementPopup(autres_moyen_paiement, self)
                if dialog.exec():
                    selected_value = dialog.get_selected_moyen_paiement()
                    UpdateMoyenPaiementInOperations(nom, selected_value)
                    UpdateMoyenPaiementTier(nom,selected_value)
                    self.load_tiers()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé

        # Suppression de la sous-catégorie
        DeleteMoyenPaiement(nom)
        self.load_tiers()
        self.load_operations()
        self.moyen_paiement_table.removeRow(row)



    def edit_selected_sous_categorie(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.sous_categorie_table.item(row, 0)
        nom = item_nom.text()
        categorie_parent = self.sous_categorie_table.item(row, 1).text()
        # Créer l'objet Tier existant
        sous_categorie = SousCategorie(nom,categorie_parent)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditSousCategorieDialog(self, sous_categorie=sous_categorie)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.sous_categorie_table.item(row, 0).setText(dialog.nom.text())
            self.sous_categorie_table.item(row, 1).setText(dialog.categorie_parent.currentText())
            self.load_tiers()
            self.load_operations()


    def edit_selected_benficiaire(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.sous_categorie2_table.item(row, 0)
        nom = item_nom.text()
        type_beneficiaire = self.sous_categorie2_table.item(row, 1).text()
        # Créer l'objet Tier existant
        beneficiaire = Beneficiaire(nom,type_beneficiaire)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditBeneficiaireDialog(self, beneficiaire=beneficiaire)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.sous_categorie2_table.item(row, 0).setText(dialog.nom.text())
            self.sous_categorie2_table.item(row, 1).setText(dialog.type_beneficiaire_parent.currentText())
            self.load_operations()

    def edit_selected_categorie(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.categorie_table.item(row, 0)
        nom = item_nom.text()
        # Créer l'objet Tier existant
        categorie = Categorie(nom)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditCategorieDialog(self, categorie=categorie)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.categorie_table.item(row, 0).setText(dialog.nom.text())
            self.load_sous_categories()
            self.load_tiers()
            self.load_operations()

    def edit_selected_type_beneficiaire(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.categorie2_table.item(row, 0)
        nom = item_nom.text()
        # Créer l'objet Tier existant
        type_beneficiaire = TypeBeneficiaire(nom)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditTypeBeneficiaireDialog(self, type_beneficiaire=type_beneficiaire)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.categorie_table.item(row, 0).setText(dialog.nom.text())
            self.load_operations()
            self.load_type_beneficiaire()

    def edit_selected_type_tier(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.type_tier_table.item(row, 0)
        nom = item_nom.text()
        # Créer l'objet Tier existant
        type_tier = TypeTier(nom)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditTypeTierDialog(self, type_tier=type_tier)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.type_tier_table.item(row, 0).setText(dialog.nom.text())
            self.load_tiers()
            self.load_operations()

    def edit_selected_historique_placement(self, row):
        # Récupérer les informations de la ligne sélectionnée
        date_int = int(datetime.strptime(self.history_table.item(row, 0).text(), "%d/%m/%Y").strftime("%Y%m%d"))
        historique_placement = GetHistoriquePlacementByDate(self.current_placement,date_int)
        historique_placement.date = self.history_table.item(row, 0).text()

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditPlacementDialog(self, placement=historique_placement,mode='modifier')
        if dialog.exec():
            self.show_placement_history_graph(self.placement_table.item(self.current_placement_row, 0))
            self.placement_table.clearContents()
            self.load_placement()
            self.account_list.clear()
            self.load_accounts()


    def delete_selected_historique_placement(self, row):
        # Récupérer les informations de la ligne sélectionnée
        choix = QMessageBox.question(
                    self,
                    "Suppression de la valeur historique du placement",
                    "La valeur historique du placement va être supprimée\nEtes-vous sûr de vouloir supprimer cette valeur ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
        if choix == QMessageBox.StandardButton.Yes:
            date_int = int(datetime.strptime(self.history_table.item(row, 0).text(), "%d/%m/%Y").strftime("%Y%m%d"))
            DeleteHistoriquePlacement(self.current_placement,date_int)
            self.show_placement_history_graph(self.placement_table.item(self.current_placement_row, 0))
            self.placement_table.clearContents()
            self.load_placement()
            self.account_list.clear()
            self.load_accounts()
        


    def edit_selected_operation(self, row, isEdit):
        try:
            # Récupère l'ID de l'opération à partir d'une colonne cachée ou d'une donnée stockée
            operation_id_item = self.transaction_table.item(row, 0)  # Assure-toi que l'ID est dans la colonne 0
            if not operation_id_item:
                return

            operation_id = operation_id_item.data(Qt.ItemDataRole.UserRole)
            if not operation_id:
                return

            # Récupérer l'objet Operation depuis la base de données
            operation = GetOperation(operation_id)
            if not operation:
                QMessageBox.warning(self, "Erreur", "Impossible de trouver l'opération sélectionnée.")
                return

            # Ouvrir le dialogue en mode édition
            dialog = AddEditOperationDialog(
            parent=self,
            account_id=self.current_account,
            operation=operation,
            isEdit=isEdit
        )
            if dialog.exec():
                # Recharger les opérations du compte courant après édition
                self.load_operations()

        except Exception as e:
            print("Erreur lors de la modification de l'opération:", e)
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def edit_selected_moyen_paiement(self, row):
        # Récupérer les informations de la ligne sélectionnée
        item_nom = self.moyen_paiement_table.item(row, 0)
        nom = item_nom.text()
        # Créer l'objet Tier existant
        moyen_paiement = MoyenPaiement(nom)

        # Ouvrir la fenêtre AddTierDialog en mode modification
        dialog = AddEditMoyenPaiementDialog(self, moyen_paiement=moyen_paiement)
        if dialog.exec():
            # Si validé : actualiser la ligne du tableau
            self.moyen_paiement_table.item(row, 0).setText(dialog.nom.text())
            self.load_tiers()
            self.load_operations()
            
    def open_performance_dialog(self):
        if self.current_account is not None:
            dialog = ShowPerformanceDialog(self, self.current_account)
            dialog.exec()

    def open_add_operation_dialog(self):
        if self.current_account is not None:
            dialog = AddEditOperationDialog(self, self.current_account)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte d'abord.")

    def open_add_position_dialog(self):
        if self.current_account is not None:
            dialog = AddPositionDialog(self, self.current_account)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte de placement d'abord.")

    def add_tier_row(self, row, tier: Tier):
            item_nom = QTableWidgetItem(tier.nom)
            item_nom.setData(Qt.ItemDataRole.UserRole, tier._id)
            self.tier_table.setItem(row, 0, item_nom)

            self.tier_table.setItem(row, 1, QTableWidgetItem(tier.type))
            self.tier_table.setItem(row, 2, QTableWidgetItem(tier.categorie))
            self.tier_table.setItem(row, 3, QTableWidgetItem(tier.sous_categorie))
            self.tier_table.setItem(row, 4, QTableWidgetItem(tier.moyen_paiement))
            self.tier_table.setItem(row, 5, QTableWidgetItem("Actif" if tier.actif else "Inactif"))



    def add_sous_categorie_row(self, row, sous_cat: SousCategorie):
        item = QTableWidgetItem(sous_cat.nom)
        item.setData(Qt.ItemDataRole.UserRole, {
            "nom": sous_cat.nom,
            "categorie_parent": sous_cat.categorie_parent
        })
        self.sous_categorie_table.setItem(row, 0, item)
        self.sous_categorie_table.setItem(row, 1, QTableWidgetItem(sous_cat.categorie_parent))

    def add_beneficiaire_row(self, row, beneficiaire: Beneficiaire):
        item = QTableWidgetItem(beneficiaire.nom)
        item.setData(Qt.ItemDataRole.UserRole,beneficiaire.nom)
        self.sous_categorie2_table.setItem(row, 0, item)
        self.sous_categorie2_table.setItem(row, 1, QTableWidgetItem(beneficiaire.type_beneficiaire))

    def add_categorie_row(self, row,categorie : Categorie):
        item = QTableWidgetItem(categorie.nom)
        item.setData(Qt.ItemDataRole.UserRole,categorie.nom)
        self.categorie_table.setItem(row, 0, item)

    def add_type_beneficiaire_row(self, row,type_beneficiaire : TypeBeneficiaire):
        item = QTableWidgetItem(type_beneficiaire.nom)
        item.setData(Qt.ItemDataRole.UserRole,type_beneficiaire.nom)
        self.categorie2_table.setItem(row, 0, item)
        

    def add_moyen_paiement_row(self, row, mp: MoyenPaiement):
        item = QTableWidgetItem(mp.nom)
        item.setData(Qt.ItemDataRole.UserRole, mp.nom)
        self.moyen_paiement_table.setItem(row, 0, item)

    def add_type_tier_row(self, row, tt: TypeTier):
        item = QTableWidgetItem(tt.nom)
        item.setData(Qt.ItemDataRole.UserRole, tt.nom)
        self.type_tier_table.setItem(row, 0, item)

    def add_placement_row(self, row, placement: HistoriquePlacement):
        self.placement_table.setItem(row, 0, align_center(QTableWidgetItem(placement.nom)))
        self.placement_table.setItem(row, 1, align_center(QTableWidgetItem(placement.type)))
        self.placement_table.setItem(row, 2, align_center(DateTableWidgetItem(placement.date)))
        self.placement_table.setItem(row, 3, align_center(NumericTableWidgetItem(placement.val_actualise, format_montant(placement.val_actualise))))
        self.placement_table.setItem(row, 4, align_center(QTableWidgetItem(placement.origine)))

    def add_compte_row(self, row, compte: Compte):
        item_nom = QTableWidgetItem(str(compte.nom))
        item_nom.setData(Qt.ItemDataRole.UserRole, str(compte._id))
        self.compte_table.setItem(row, 0, item_nom)

        solde = compte.solde
        solde_str = f"{solde:,.2f}".replace(",", " ").replace(".", ",") + " €"
        if solde < 0:
            solde_str = solde_str.replace("-", "- ")
            color = QColor("red")
        else:
            solde_str = "+ " + solde_str
            color = QColor("green")
        
        item_solde = NumericTableWidgetItem(solde, solde_str)
        item_solde.setForeground(color)
        item_solde.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.compte_table.setItem(row, 1, item_solde)
        self.compte_table.setItem(row, 2, QTableWidgetItem(compte.type))
        self.compte_table.setItem(row, 3, QTableWidgetItem(compte.nom_banque))

        
    def load_operations(self, operations=None, solde=None):
        if self.current_account is None:
            return 
        if operations is None or solde is None:
            operations = GetOperationsNotBq(self.current_account)
            solde = GetDerniereValeurPointe(self.current_account)[0]

        self.transaction_table.setRowCount(0)
        self._populate_transaction_table(operations, solde)
        self.transaction_table.sortItems(0,Qt.SortOrder.AscendingOrder)

    def _populate_transaction_table(self, operations: list, initial_solde: float):
        self.transaction_table.setSortingEnabled(False)
        solde = initial_solde
        rows = []
        for operation in operations:
            row_data = self._create_transaction_row_data(operation, solde)
            solde = row_data.pop('solde')
            rows.append(row_data)

        self.transaction_table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            self._add_row_to_table(row_index, row_data)

        self.transaction_table.resizeColumnsToContents()
        self.transaction_table.setSortingEnabled(True)

    def _create_transaction_row_data(self, operation: 'Operation', previous_solde: float) -> dict:
        tier_name = self.get_tier_name(operation.tier)
        compte_name = self.get_compte_name(operation.compte_id) if operation.compte_id else ''
        compte_associe_name = self.get_compte_name(operation.compte_associe) if operation.compte_associe else ''

        date_item = DateTableWidgetItem(operation.date)
        date_item.setData(Qt.ItemDataRole.UserRole, operation._id)

        row_data = {
            0: date_item,
            1: QTableWidgetItem(operation.type),
            2: QTableWidgetItem(compte_name),
            3: QTableWidgetItem(compte_associe_name),
            4: QTableWidgetItem(operation.type_tier),
            5: QTableWidgetItem(tier_name),
            6: QTableWidgetItem(operation.type_beneficiaire),
            7: QTableWidgetItem(operation.beneficiaire),
            8: QTableWidgetItem(operation.moyen_paiement),
            9: QTableWidgetItem(str(operation.num_cheque) if operation.num_cheque is not None else ""),
            10: QTableWidgetItem('R' if operation.bq else ""),
            11: QTableWidgetItem(operation.categorie),
            12: QTableWidgetItem(operation.sous_categorie),
            15: QTableWidgetItem(operation.notes),
            13: QTableWidgetItem(""),  # Debit column, might be overwritten
            14: QTableWidgetItem(""),  # Credit column, might be overwritten
        }

        if operation.type.lower() in ["débit", "transfert vers"]:
            debit_formate = f"{operation.debit:,.2f}".replace(",", " ").replace(".", ",").replace("-", "- ") + " €" if operation.debit < 0 else ""
            debit_item = NumericTableWidgetItem(operation.debit, debit_formate)
            debit_item.setForeground(QColor("red"))
            debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_data[13] = debit_item
        elif operation.type.lower() in ["crédit", "transfert de"]:
            credit_formate = f"+ {operation.credit:,.2f}".replace(",", " ").replace(".", ",") + " €" if operation.credit > 0 else ""
            credit_item = NumericTableWidgetItem(operation.credit, credit_formate)
            credit_item.setForeground(QColor("green"))
            credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_data[14] = credit_item

        solde = previous_solde + operation.debit + operation.credit
        solde_formate = f"{solde:,.2f}".replace(",", " ").replace(".", ",")
        if solde < 0:
            solde_formate = solde_formate.replace("-","- ") + " €"
            solde_item = NumericTableWidgetItem(solde, solde_formate)
            solde_item.setForeground(QColor("red"))
        else:
            solde_formate = "+ " + solde_formate + " €"
            solde_item = NumericTableWidgetItem(solde, solde_formate)
            solde_item.setForeground(QColor("green"))
        solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row_data[16] = solde_item
        row_data['solde'] = solde
        return row_data

    def _add_row_to_table(self, row_index: int, row_data: dict):
        for col, item in row_data.items():
            self.transaction_table.setItem(row_index, col, item)

    def add_operation(self, operation):
        InsertOperation(operation)
        if  not self.pointage_state['suspendu']:
            self.load_operations()
        else :
            # Récupérer toutes les opérations de nouveau
            operations = GetOperationsNotBq(self.current_account)
            solde_depart = GetDerniereValeurPointe(self.current_account)[0]

            # Recharger le tableau depuis le solde de départ
            self.transaction_table.setRowCount(0)
            self._populate_transaction_table(operations, solde_depart)

            # Réappliquer les styles sur les lignes déjà pointées
            for row in self.pointage_state['rows']:
                self.transaction_table.selectRow(row)
                self.transaction_table.item(row, 9).setText("P")  # Colonne Bq
        self.account_list.clear()
        self.load_accounts()
        self.compte_table.clearContents()
        self.load_comptes()
        self.sound_effect("sound_effect/transaction.mp3")

    def sound_effect(self,sound_path:str):
        sound_path = os.path.abspath(sound_path)
        if os.path.exists(sound_path):
            self.player.setAudioOutput(self.audio_output)
            self.player.setSource(QUrl.fromLocalFile(sound_path))
            self.audio_output.setVolume(50)  # Volume entre 0 et 100
            self.player.play()
        else:
            print(f"Fichier son introuvable : {sound_path}")



    def add_position_row(self, position: Position):
        compte_associe_name = ''
        if position.compte_associe != '':
            compte_associe_name = self.get_compte_name(position.compte_associe)
            
        self.position_table.setSortingEnabled(False)
        row = self.position_table.rowCount()
        self.position_table.insertRow(row)
        self.position_table.setItem(row, 0, align_center(DateTableWidgetItem(position.date)))
        self.position_table.setItem(row, 1, align_center(QTableWidgetItem(position.type)))
        self.position_table.setItem(row, 2, align_center(QTableWidgetItem(compte_associe_name)))
        self.position_table.setItem(row, 3, align_center(QTableWidgetItem(position.nom_placement)))
        self.position_table.setItem(row, 4, align_center(NumericTableWidgetItem(position.nb_part, str(position.nb_part))))
        self.position_table.setItem(row, 5, align_center(NumericTableWidgetItem(position.val_part, format_montant(position.val_part))))
        self.position_table.setItem(row, 6, align_center(NumericTableWidgetItem(position.frais, format_montant(position.frais))))
        self.position_table.setItem(row, 7, align_center(NumericTableWidgetItem(position.interets, format_montant(position.interets))))
        self.position_table.setItem(row, 8, align_center(QTableWidgetItem(position.notes)))
        self.position_table.setItem(row, 9, align_center(NumericTableWidgetItem(position.montant_investit, format_montant(position.montant_investit))))

        self.position_table.resizeColumnsToContents()
        self.position_table.setSortingEnabled(True)

    
    def add_position(self, position:Position):
        InsertPosition(position)
        if position.type == "Achat":
            InsertOperation(Operation(position.date,TypeOperation.TransfertV.value,"","","","","",round(position.nb_part*position.val_part * -1),0,f"Achat de {position.nb_part} parts de {position.nom_placement} à {position.val_part} €",position.compte_associe,compte_associe=position.compte_id))
        type_placement = GetTypePlacement(position.nom_placement)
        last_value_placement = GetLastValueForPlacement(position.nom_placement)
        if not InsertHistoriquePlacement(HistoriquePlacement(position.nom_placement, type_placement, position.date, position.val_part, position.type)) and last_value_placement != position.val_part:
            # Ici on suppose que le conflit est dû à un doublon. Tu peux filtrer plus précisément avec l'erreur SQL si nécessaire.
            conflit_msg = QMessageBox()
            conflit_msg.setWindowTitle("Conflit détecté")
            date_str = str(position.date)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            display_date = QDate(year, month, day).toString("dd/MM/yyyy")
            conflit_msg.setText(f"Une entrée pour ce placement existe déjà. (date : {display_date}, valeur connue : {last_value_placement} € )")
            conflit_msg.setInformativeText("Voulez-vous remplacer l'ancienne valeur par la nouvelle ?")
            conflit_msg.setIcon(QMessageBox.Icon.Warning)
            conflit_msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            conflit_msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            result = conflit_msg.exec()

            if result == QMessageBox.StandardButton.Yes:
                # Remplace l'ancienne valeur (mise à jour dans la BDD)
                DeleteHistoriquePlacement(position.nom_placement,position.date)
                InsertHistoriquePlacement(HistoriquePlacement(position.nom_placement, type_placement, position.date, position.val_part, position.type))
                QMessageBox.information(None, "Mise à jour", "L'opération a été mise à jour avec succès.")
            else:
                # Ne rien faire, l'utilisateur a choisi de garder l'existant
                QMessageBox.information(None, "Annulé", "L'opération existante a été conservée.")
        self.sound_effect("sound_effect/transaction.mp3")
        self.account_list.clear()
        self.load_accounts()
        self.add_position_row(position)
        self.compte_table.clearContents()
        self.load_comptes()
        self.placement_table.clearContents()
        self.load_placement()

    def add_tier(self, tier: Tier):
        InsertTier(tier)

        # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
        self.tier_table.setSortingEnabled(False)

        # 2. Ajoute la nouvelle ligne
        row = self.tier_table.rowCount()
        self.tier_table.setRowCount(row + 1)
        self.add_tier_row(row, tier)

        # 3. Ajuste la largeur des colonnes puis réactive le tri
        self.tier_table.resizeColumnsToContents()
        self.tier_table.setSortingEnabled(True)
        self.tiers_filter.addItem(tier.nom)
        self.tiers_nom_to_id[tier.nom] = str(tier._id)
        
    def add_sous_categorie(self,sous_categorie):
        if InsertSousCategorie(sous_categorie):
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.sous_categorie_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.sous_categorie_table.rowCount()
            self.sous_categorie_table.setRowCount(row + 1)
            self.add_sous_categorie_row(row, sous_categorie)

            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.sous_categorie_table.resizeColumnsToContents()
            self.sous_categorie_table.setSortingEnabled(True)
            self.sous_categorie_filter.addItem(sous_categorie.nom)

    def add_beneficiaire(self,beneficiaire):
        if InsertBeneficiaire(beneficiaire):
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.sous_categorie2_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.sous_categorie2_table.rowCount()
            self.sous_categorie2_table.setRowCount(row + 1)
            self.add_beneficiaire_row(row, beneficiaire)

            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.sous_categorie2_table.resizeColumnsToContents()
            self.sous_categorie2_table.setSortingEnabled(True)

    def add_categorie(self,categorie):
        if InsertCategorie(categorie):
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.categorie_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.categorie_table.rowCount()
            self.categorie_table.setRowCount(row + 1)
            self.add_categorie_row(row, categorie)

            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.categorie_table.resizeColumnsToContents()
            self.categorie_table.setSortingEnabled(True)
            self.categorie_filter.addItem(categorie.nom)

    def add_type_beneficiaire(self,type_beneficiaire:TypeBeneficiaire):
        if InsertTypeBeneficiaire(type_beneficiaire):
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.categorie2_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.categorie2_table.rowCount()
            self.categorie2_table.setRowCount(row + 1)
            self.add_type_beneficiaire_row(row, type_beneficiaire)

            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.categorie2_table.resizeColumnsToContents()
            self.categorie2_table.setSortingEnabled(True)

    def add_type_tier(self,type_tier):
        if InsertTypeTier(type_tier,parent=self):
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.type_tier_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.type_tier_table.rowCount()
            self.type_tier_table.setRowCount(row + 1)
            self.add_type_tier_row(row,type_tier)
            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.type_tier_table.resizeColumnsToContents()
            self.type_tier_table.setSortingEnabled(True)
            

    def add_placement(self,historique_placement:HistoriquePlacement):
        placement = Placement(historique_placement.nom,historique_placement.type)
        if InsertPlacement(placement,parent=self):
            InsertHistoriquePlacement(historique_placement)
            self.account_list.clear()
            self.load_accounts()
            self.compte_table.clearContents()
            self.load_comptes()
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.placement_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.placement_table.rowCount()
            self.placement_table.setRowCount(row + 1)
            self.add_placement_row(row,historique_placement)
            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.placement_table.resizeColumnsToContents()
            self.placement_table.setSortingEnabled(True)

    def add_moyen_paiement(self,moyen_paiement):
        if InsertMoyenPaiement(moyen_paiement,parent=self):
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.moyen_paiement_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.moyen_paiement_table.rowCount()
            self.moyen_paiement_table.setRowCount(row + 1)
            self.add_moyen_paiement_row(row,moyen_paiement)
            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.moyen_paiement_table.resizeColumnsToContents()
            self.moyen_paiement_table.setSortingEnabled(True)
            

    def add_compte(self,compte:Compte):
        if InsertCompte(compte,parent=self):                    
            self.account_list.clear()
            self.load_accounts()
            # 1. Suspend le tri pour empêcher le déplacement de la ligne en cours d’édition
            self.compte_table.setSortingEnabled(False)

            # 2. Ajoute la nouvelle ligne
            row = self.compte_table.rowCount()
            self.compte_table.setRowCount(row + 1)
            self.add_compte_row(row,compte)
            # 3. Ajuste la largeur des colonnes puis réactive le tri
            self.compte_table.resizeColumnsToContents()
            self.compte_table.setSortingEnabled(True)
            self.compte_filter.addItem(compte.nom)
            self.comptes_nom_to_id[compte.nom] = str(compte._id)
            
            

    def update_tier(self, tier):
        UpdateTier(tier)

    def update_sous_categorie(self, sous_categorie,old_nom):
        UpdateSousCategorie(sous_categorie,old_nom)

    def update_beneficiaire(self, beneficiaire,old_nom):
        UpdateBeneficiaire(beneficiaire,old_nom)

    def update_categorie(self, categorie,old_nom):
        UpdateCategorie(categorie,old_nom)

    def update_type_beneficiaire(self, type_beneficiare,old_nom):
        UpdateTypeBeneficiaire(type_beneficiare,old_nom)

    def update_type_tier(self, type_tier,old_nom):
        UpdateTypeTypeTier(type_tier,old_nom)

    def update_placement(self, placement,old_nom):
        UpdatePlacement(placement,old_nom)

    def update_moyen_paiement(self, moyen_paiement,old_nom):
        UpdateMoyenPaiement(moyen_paiement,old_nom)

    def update_account(self, compte):
        UpdateCompte(compte)
        self.account_list.clear()
        self.load_accounts()

    def update_operation(self, operation:Operation,old_credit,old_debit,isEdit):
        if isEdit:
            DeleteOperation(operation,old_credit,old_debit)
            InsertOperation(operation)
        else:
            operation._id = str(ObjectId())
            operation.bq = 0
            InsertOperation(operation)
            self.sound_effect("sound_effect/transaction.mp3")
        self.account_list.clear()
        self.load_accounts()
        self.load_operations()

    def show_about(self):
        QMessageBox.information(self, "À propos", "Money Manager v0.1\nCréé avec PyQt6.")
    
    @staticmethod    
    def get_tier_name(tier_id: Optional[str]) -> str:
        if not tier_id:
            return ""
        tier_name = GetTierName(tier_id)
        return tier_name if tier_name else ""
    
    @staticmethod    
    def get_compte_name(compte_id: Optional[str]) -> str:

        return GetCompteName(compte_id)


    def setup_accueil_tab(self):
        accueil_tab_layout = QHBoxLayout(self.accueil_tab)

        # Panel - Accounts
        panel = QVBoxLayout()
        self.account_list = QListWidget()
        self.load_accounts()

        self.account_list.itemClicked.connect(self.on_account_clicked)

        add_account_btn = QPushButton("Ajouter un compte")
        add_account_btn.clicked.connect(self.open_add_account_dialog)

        panel.addWidget(QLabel("Comptes:"))
        panel.addWidget(self.account_list)
        panel.addWidget(add_account_btn)

        panel_widget = QWidget()
        panel_widget.setLayout(panel)
        panel_widget.setMaximumWidth(500)

        accueil_tab_layout.addWidget(panel_widget)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        accueil_tab_layout.addItem(spacer)

    def setup_operation_tab(self):
        operation_tab_layout = QHBoxLayout(self.operation_tab)

        # Right Panel - Transactions / Placements
        right_panel = QVBoxLayout()

        self.transaction_table = QTableWidget(0, 17)
        self.transaction_table.setHorizontalHeaderLabels([
            "Date", "Type\nOpération","Compte", "Compte\nAssocié", "Type\nde\nTiers", "Tiers","Type\nBénéficiaire", "Bénéficiaire",
            "Moyen\nPaiement", "Numéro\nchèque", "Bq", "Catégorie", "Sous-\nCatégorie",
            "Débit", "Crédit", "Note", "Solde"
        ])
        self.transaction_table.horizontalHeader().setStretchLastSection(True)
        self.transaction_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.transaction_table.setSortingEnabled(True)
        self.transaction_table.setAlternatingRowColors(True)
        self.transaction_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.transaction_table.customContextMenuRequested.connect(self.show_context_menu_operation)
        self.transaction_table.cellClicked.connect(self.handle_table_click)

        self.position_table = QTableWidget(0, 10)
        self.position_table.setHorizontalHeaderLabels([
            "Date", "Type", "Compte Associé", "Placement", "Nombre parts", "Valeur part", "Frais", "Intérêts", "Notes", "Montant Investissement"
        ])
        self.position_table.horizontalHeader().setStretchLastSection(True)
        self.position_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.position_table.setSortingEnabled(True)
        self.position_table.setAlternatingRowColors(True)

        # Stack pour alterner entre transactions et placements
        self.table_stack = QStackedLayout()
        self.table_stack.addWidget(self.transaction_table)  # index 0
        self.table_stack.addWidget(self.position_table)    # index 1

        self.add_transaction_btn = QPushButton("Ajouter une transaction")
        self.add_transaction_btn.clicked.connect(self.open_add_operation_dialog)

        self.show_performance_btn = QPushButton("Voir les performances")
        self.show_performance_btn.clicked.connect(self.open_performance_dialog)

        self.pointage_btn = QPushButton("Commencer le pointage")
        self.pointage_btn.clicked.connect(self.commencer_pointage)

        self.suspendre_pointage_btn = QPushButton("Suspendre le pointage")
        self.suspendre_pointage_btn.clicked.connect(self.suspendre_pointage)
        self.suspendre_pointage_btn.hide()

        self.reprendre_pointage_btn = QPushButton("Reprendre le pointage")
        self.reprendre_pointage_btn.clicked.connect(self.reprendre_pointage)
        self.reprendre_pointage_btn.hide()

        self.pointage_info_label = QLabel()
        self.pointage_info_label.setStyleSheet("font-weight: bold; color: #0055AA;")
        self.pointage_info_label.hide()  # caché tant qu'on ne commence pas

        self.end_pointage_btn = QPushButton("Terminer le pointage")
        self.end_pointage_btn.clicked.connect(self.terminer_pointage)
        self.end_pointage_btn.hide()  # Masqué par défaut
        self.cancel_pointage_btn = QPushButton("Annuler le pointage")
        self.cancel_pointage_btn.clicked.connect(self.annuler_pointage)
        self.cancel_pointage_btn.hide()  # Masqué par défaut

        

        # Layout horizontal pour les deux boutons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_transaction_btn)
        button_layout.addWidget(self.show_performance_btn)
        button_layout.addWidget(self.pointage_btn)        
        button_layout.addWidget(self.cancel_pointage_btn)
        button_layout.addWidget(self.suspendre_pointage_btn)
        button_layout.addWidget(self.reprendre_pointage_btn)
        button_layout.addWidget(self.end_pointage_btn)
        button_layout.addWidget(self.pointage_info_label)
        self.show_performance_btn.hide()  # Toujours masqué par défaut
       # --- Filtres ---
        self.cats_label = QLabel()
        self.sous_cats_label = QLabel()
        self.tiers_label = QLabel()
        filter_layout = QGridLayout()


        self.bq_filter = QCheckBox()
        self.bq_filter.setTristate(True)
        self.bq_filter.setCheckState(Qt.CheckState.PartiallyChecked)

        self.date_debut_filter = CustomDateEdit()
        self.date_debut_filter.setDate(QDate.currentDate().addMonths(-1))  # Par défaut, 1 mois avant

        self.date_fin_filter = CustomDateEdit()
        self.date_fin_filter.setDate(QDate.currentDate())  # Aujourd'hui

        self.tiers_filter = CheckableComboBox()
        self.tiers_filter.setPlaceholderText("Selectionner...")
        self.tiers_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.tiers_filter.addSpecialItem("Tout désélectionner", "deselect_all")

        # Récupère les noms des tiers
        tiers_noms = [tier.nom for tier in GetTiers()]
        self.tiers_nom_to_id = {}

        # Ajout dans le combo
        for tier in GetTiers():
            self.tiers_filter.addItem(tier.nom)
            self.tiers_nom_to_id[tier.nom] = str(tier._id)
        # Configure le completer
        tiers_completer = QCompleter(tiers_noms, self)
        tiers_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        tiers_completer.setFilterMode(Qt.MatchFlag.MatchContains)

        # Attache le completer au champ
        self.tiers_filter.setCompleter(tiers_completer)

        # Tu peux alimenter ces ComboBox avec tes vraies données plus tard
        self.categorie_filter = CheckableComboBox(self)
        self.categorie_filter.setPlaceholderText("Selectionner...")
        self.categorie_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.categorie_filter.addSpecialItem("Tout désélectionner", "deselect_all")
        self.sous_categorie_filter = CheckableComboBox(self)
        self.sous_categorie_filter.setPlaceholderText("Selectionner...")
        self.sous_categorie_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.sous_categorie_filter.addSpecialItem("Tout désélectionner", "deselect_all")

        # Remplir les catégories
        for cat in GetCategorie():
            self.categorie_filter.addItem(cat.nom)
            for sous_cat in GetSousCategorie(cat.nom):
                self.sous_categorie_filter.addItem(sous_cat.nom)

        self.compte_filter = CheckableComboBox()
        self.compte_filter.setPlaceholderText("Selectionner...")
        self.compte_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.compte_filter.addSpecialItem("Tout désélectionner", "deselect_all")

        self.comptes_nom_to_id = {}
        for compte in GetComptes():
            self.compte_filter.addItem(compte.nom)
            self.comptes_nom_to_id[compte.nom] = str(compte._id)

        apply_filter_btn = QPushButton("Appliquer les filtres")
        apply_filter_btn.clicked.connect(self.apply_filters)
        self.reset_filter_button = QPushButton("Réinitialiser les filtres")
        self.reset_filter_button.clicked.connect(self.reset_filters)

        filter_layout.addWidget(QLabel("Date début:"), 0, 0)
        filter_layout.addWidget(self.date_debut_filter, 0, 1)
        filter_layout.addWidget(QLabel("Date fin:"), 0, 2)
        filter_layout.addWidget(self.date_fin_filter, 0, 3)
        filter_layout.addWidget(QLabel("Pointées:"),0,4)
        filter_layout.addWidget(self.bq_filter,0,5)

        # --- Filtres principaux (dates, pointées) ---
        right_panel.addLayout(filter_layout)  # Tu peux garder le layout grille pour les filtres date & pointées

        # --- Filtres avancés (tiers, catégorie, sous-catégorie + boutons) ---

        # Colonne Tiers
        tiers_col = QHBoxLayout()
        tiers_col.addWidget(QLabel("Tiers:"))
        tiers_col.addWidget(self.tiers_filter)

        comptes_col = QHBoxLayout()
        comptes_col.addWidget(QLabel("Comptes:"))
        comptes_col.addWidget(self.compte_filter)

        # Colonne Catégorie
        cat_col = QHBoxLayout()
        cat_col.addWidget(QLabel("Catégorie:"))
        cat_col.addWidget(self.categorie_filter)

        # Colonne Sous-Catégorie
        sous_cat_col = QHBoxLayout()
        sous_cat_col.addWidget(QLabel("Sous-catégorie:"))
        sous_cat_col.addWidget(self.sous_categorie_filter)
        # Filtres combinés
        filter_selection_layout = QHBoxLayout()
        filter_selection_layout.addLayout(tiers_col)
        filter_selection_layout.addLayout(comptes_col)
        filter_selection_layout.addLayout(cat_col)
        filter_selection_layout.addLayout(sous_cat_col)

        # --- Ligne boutons Appliquer / Réinitialiser ---
        apply_reset_layout = QHBoxLayout()
        apply_filter_btn = QPushButton("Appliquer les filtres")
        apply_filter_btn.clicked.connect(self.apply_filters)

        reset_filter_button = QPushButton("Réinitialiser les filtres")
        reset_filter_button.clicked.connect(self.reset_filters)

        apply_reset_layout.addWidget(apply_filter_btn)
        apply_reset_layout.addWidget(reset_filter_button)

        # Ajout à l'interface
        right_panel.addLayout(filter_selection_layout)
        right_panel.addLayout(apply_reset_layout)

        right_panel.addLayout(filter_layout)

        right_panel.addLayout(self.table_stack)
        right_panel.addLayout(button_layout)
        
        operation_tab_layout.addLayout(right_panel, 3)

    def select_all_items(self, combo: CheckableComboBox, checked: bool):
        for i in range(combo.model().rowCount()):
            item = combo.model().item(i)
            if item is not None:
                item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        combo.update_display_text()  # Met à jour le texte affiché dans le champ

    def setup_tiers_tab(self):
        layout = QHBoxLayout(self.tier_tab)

        tiers_section = QVBoxLayout()
        self.tier_table = QTableWidget(0, 6)
        self.tier_table.setHorizontalHeaderLabels(["Nom", "Type", "Catégorie", "Sous-\ncatégorie.", "Moyen\nde\npaiement", "Actif"])
        self.tier_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tier_table.setAlternatingRowColors(True)
        self.tier_table.setSortingEnabled(True)
        self.tier_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tier_table.customContextMenuRequested.connect(self.show_context_menu_tier)
        tiers_section.addWidget(QLabel("Tiers:"))
        tiers_section.addWidget(self.tier_table)
        add_btn = QPushButton("Ajouter un tier")
        add_btn.clicked.connect(self.open_add_tier_dialog)
        tiers_section.addWidget(add_btn)

        types_section = QVBoxLayout()
        self.type_tier_table = QTableWidget(0, 1)
        self.type_tier_table.setHorizontalHeaderLabels(["Type\nde\nTiers"])
        self.type_tier_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.type_tier_table.setAlternatingRowColors(True)
        self.type_tier_table.setSortingEnabled(True)
        self.type_tier_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.type_tier_table.customContextMenuRequested.connect(self.show_context_menu_type_tier)
        types_section.addWidget(QLabel("Types de Tier:"))
        types_section.addWidget(self.type_tier_table)
        add_type_btn = QPushButton("Ajouter type de tier")
        add_type_btn.clicked.connect(self.open_add_type_tier_dialog)
        types_section.addWidget(add_type_btn)

        layout.addLayout(tiers_section)
        layout.addLayout(types_section)
        self.load_tiers()
        self.load_type_tier()

    def setup_categories_tab(self):
        layout = QHBoxLayout(self.categories_tab)

        cat_section = QVBoxLayout()
        self.categorie_table = QTableWidget(0, 1)
        self.categorie_table.setHorizontalHeaderLabels(["Catégorie"])
        self.categorie_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.categorie_table.setAlternatingRowColors(True)
        self.categorie_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.categorie_table.customContextMenuRequested.connect(self.show_context_menu_categorie)
        cat_section.addWidget(QLabel("Catégories:"))
        cat_section.addWidget(self.categorie_table)
        add_btn = QPushButton("Ajouter catégorie")
        add_btn.clicked.connect(self.open_add_categorie_dialog)
        cat_section.addWidget(add_btn)

        sous_cat_section = QVBoxLayout()
        self.sous_categorie_table = QTableWidget(0, 2)
        self.sous_categorie_table.setHorizontalHeaderLabels(["Sous-Catégorie", "Catégorie"])
        self.sous_categorie_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sous_categorie_table.setAlternatingRowColors(True)
        self.sous_categorie_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sous_categorie_table.customContextMenuRequested.connect(self.show_context_menu_sous_categorie)
        sous_cat_section.addWidget(QLabel("Sous-Catégories:"))
        sous_cat_section.addWidget(self.sous_categorie_table)
        add_btn2 = QPushButton("Ajouter sous-catégorie")
        add_btn2.clicked.connect(self.open_add_sous_categorie_dialog)
        sous_cat_section.addWidget(add_btn2)

        layout.addLayout(cat_section)
        layout.addLayout(sous_cat_section)

        self.load_categorie()
        self.load_sous_categories()


    def setup_comptes_tab(self):
        layout = QVBoxLayout(self.comptes_tab)
        self.compte_table = QTableWidget(0, 4)
        self.compte_table.setHorizontalHeaderLabels(["Nom", "Solde", "Type", "Etablissement Bancaire"])
        self.compte_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.compte_table.setAlternatingRowColors(True)
        self.compte_table.setSortingEnabled(True)
        self.compte_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.compte_table.customContextMenuRequested.connect(self.show_context_menu_compte)
        layout.addWidget(QLabel("Comptes:"))
        layout.addWidget(self.compte_table)
        add_btn = QPushButton("Ajouter un compte")
        add_btn.clicked.connect(self.open_add_account_dialog)
        layout.addWidget(add_btn)
        self.load_comptes()

    def setup_categories2_tab(self):
        layout = QHBoxLayout(self.categories2_tab)

        cat2_section = QVBoxLayout()
        self.categorie2_table = QTableWidget(0, 1)
        self.categorie2_table.setHorizontalHeaderLabels(["Type Bénéficiaire"])
        self.categorie2_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.categorie2_table.setAlternatingRowColors(True)
        self.categorie2_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.categorie2_table.customContextMenuRequested.connect(self.show_context_menu_type_beneficiaire)
        cat2_section.addWidget(QLabel("Type Bénéficiaire:"))
        cat2_section.addWidget(self.categorie2_table)
        btn_cat2 = QPushButton("Ajouter un type de bénéficiaire")
        btn_cat2.clicked.connect(self.open_add_type_beneficiaire_dialog)
        cat2_section.addWidget(btn_cat2)

        sous_cat2_section = QVBoxLayout()
        self.sous_categorie2_table = QTableWidget(0, 2)
        self.sous_categorie2_table.setHorizontalHeaderLabels(["Bénéficiaire", "Type bénéficiaire"])
        self.sous_categorie2_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sous_categorie2_table.setAlternatingRowColors(True)
        self.sous_categorie2_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sous_categorie2_table.customContextMenuRequested.connect(self.show_context_menu_sous_categorie2)
        sous_cat2_section.addWidget(QLabel("Bénéficiaire:"))
        sous_cat2_section.addWidget(self.sous_categorie2_table)
        btn_sous_cat2 = QPushButton("Ajouter un bénéficiaire")
        btn_sous_cat2.clicked.connect(self.open_add_beneficiaire_dialog)
        sous_cat2_section.addWidget(btn_sous_cat2)

        layout.addLayout(cat2_section)
        layout.addLayout(sous_cat2_section)

        self.load_type_beneficiaire()
        self.load_beneficiaire()

    def show_placement_history_graph(self, item):
        row = item.row()
        nom = self.placement_table.item(row, 0).text()
        self.current_placement = nom
        self.current_placement_row = row

        historique = GetHistoriquePlacement(nom)
        if not historique:
            self.graph_view.setHtml("<p>Aucune donnée historique disponible.</p>")
            return

        dates = [f"{str(h.date)[6:8]}/{str(h.date)[4:6]}/{str(h.date)[0:4]}" for h in historique]
        valeurs = [h.val_actualise for h in historique]

        self.history_table.setRowCount(0)  # Réinitialiser
        for date, valeur in zip(dates,valeurs):
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            self.history_table.setItem(row_position, 0, QTableWidgetItem(date))
            valeur_formate = f"{valeur:,.2f}".replace(",", " ").replace(".", ",").replace("-", "- ") + " €"
            valeur_item = NumericTableWidgetItem(valeur, valeur_formate)
            valeur_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_table.setItem(row_position, 1, valeur_item)
        
        self.history_table.resizeColumnsToContents()

        self.history_table.setVisible(True)
        self.history_label.setVisible(True)

        fig = go.Figure(data=[go.Scatter(x=dates, y=valeurs, mode='lines+markers', name=nom)])

        is_dark = self.palette().color(self.backgroundRole()).value() < 128
        bg_color = "#1e1e1e" if is_dark else "#ffffff"
        font_color = "#ffffff" if is_dark else "#000000"

        fig.update_layout(
            title=f"Évolution de {nom}",
            xaxis_title='Date',
            yaxis_title='Valeur',
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font=dict(color=font_color)
        )

        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>body {{ margin: 0; background-color: {bg_color}; }}</style>
        </head>
        <body>
            <div id="graph" style="width:100%; height:100%; max-height:300px;"></div>
            <script>
                var graphData = {graph_json};
                Plotly.newPlot('graph', graphData.data, graphData.layout);
            </script>
        </body>
        </html>
        """
        self.graph_view.setHtml(html, QUrl("about:blank"))


    def setup_placement_tab(self):
        # === Layout principal vertical ===
        placement_layout = QVBoxLayout(self.placement_tab)

        # === 1. Layout horizontal contenant le tableau de placements et le tableau historique ===
        placement_main_panel = QHBoxLayout()

        # -- Tableau principal des placements --
        placement_table_panel = QVBoxLayout()
        self.placement_table = QTableWidget(0, 5)
        self.placement_table.setHorizontalHeaderLabels(["Nom", "Type", "Date", "Valeur actualisée", "Origine"])
        self.placement_table.horizontalHeader().setStretchLastSection(True)
        self.placement_table.setAlternatingRowColors(True)
        self.placement_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.placement_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.placement_table.customContextMenuRequested.connect(self.show_context_menu_placement)
        self.placement_table.itemClicked.connect(self.show_placement_history_graph)

        add_placement_btn = QPushButton("Ajouter Placement")
        add_placement_btn.clicked.connect(self.open_add_placement_dialog)

        placement_table_panel.addWidget(QLabel("Placement:"))
        placement_table_panel.addWidget(self.placement_table)
        placement_table_panel.addWidget(add_placement_btn)

        # -- Panneau historique avec un layout vertical contenant le label + tableau --
        history_panel = QVBoxLayout()
        self.history_label = QLabel("Historique du placement:")
        self.history_label.setVisible(False)  # Caché initialement

        self.history_table = QTableWidget(0, 2)
        self.history_table.setHorizontalHeaderLabels(["Date", "Valeur"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setMinimumWidth(250)
        self.history_table.setVisible(False)  # Caché initialement
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu_historique_placement)

        history_panel.addWidget(self.history_label)
        history_panel.addWidget(self.history_table)

        # Ajout au layout horizontal principal
        placement_main_panel.addLayout(placement_table_panel, stretch=3)
        placement_main_panel.addLayout(history_panel, stretch=1)

        # Ajout au layout principal vertical
        placement_layout.addLayout(placement_main_panel)

        # === 2. Web view pour le graphique en bas ===
        self.graph_view = QWebEngineView()
        self.graph_view.setMinimumHeight(250)
        self.graph_view.setHtml("<h3>Sélectionnez un placement pour voir l'historique.</h3>")
        placement_layout.addWidget(self.graph_view)

        self.load_placement()

    def add_total_to_list(self):
        total = sum(compte.solde for compte in GetComptes())
        
        widget = QWidget()
        layout = QHBoxLayout(widget)

        name_label = QLabel("Total")
        name_label.setStyleSheet("font-weight: bold;")
        solde_label = QLabel(f"{total:,.2f} €".replace(",", " "))
        solde_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if total > 0:
            solde_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            solde_label.setStyleSheet("font-weight: bold; color: red;")

        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(solde_label)
        layout.setContentsMargins(5, 2, 5, 2)

        item = QListWidgetItem(self.account_list)
        item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non sélectionnable
        item.setSizeHint(widget.sizeHint())
        self.account_list.addItem(item)
        self.account_list.setItemWidget(item, widget)

    def show_context_menu_tier(self, pos: QPoint):
        item = self.tier_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_tier(row))
        delete_action.triggered.connect(lambda: self.delete_selected_tier(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.tier_table.viewport().mapToGlobal(pos))

    def show_context_menu_compte(self, pos: QPoint):
        item = self.compte_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_compte(row))
        delete_action.triggered.connect(lambda: self.delete_selected_compte(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.compte_table.viewport().mapToGlobal(pos))

    def delete_row(self, row):
        reply = QMessageBox.question(
            self, "Confirmation", "Supprimer ce tier ?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.dele(row)  # méthode à implémenter

    def show_context_menu_sous_categorie(self, pos: QPoint):
        item = self.sous_categorie_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_sous_categorie(row))
        delete_action.triggered.connect(lambda: self.delete_selected_sous_categorie(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.sous_categorie_table.viewport().mapToGlobal(pos))


    def show_context_menu_sous_categorie2(self, pos: QPoint):
        item = self.sous_categorie2_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_benficiaire(row))
        delete_action.triggered.connect(lambda: self.delete_selected_beneficiaire(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.sous_categorie2_table.viewport().mapToGlobal(pos))


    def show_context_menu_categorie(self, pos: QPoint):
        item = self.categorie_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_categorie(row))
        delete_action.triggered.connect(lambda: self.delete_selected_categorie(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.categorie_table.viewport().mapToGlobal(pos))

    def show_context_menu_type_beneficiaire(self, pos: QPoint):
        item = self.categorie2_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_type_beneficiaire(row))
        delete_action.triggered.connect(lambda: self.delete_selected_type_beneficiaire(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.categorie_table.viewport().mapToGlobal(pos))

    def show_context_menu_placement(self, pos: QPoint):
        item = self.placement_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)
        actualiser_action = QAction("Actualiser",self)

        edit_action.triggered.connect(lambda: self.edit_selected_placement(row))
        delete_action.triggered.connect(lambda: self.delete_selected_placement(row))
        actualiser_action.triggered.connect(lambda: self.actualiser_selected_placement(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(actualiser_action)
        
        menu.exec(self.placement_table.viewport().mapToGlobal(pos))

    def show_context_menu_moyen_paiement(self, pos: QPoint):
        item = self.moyen_paiement_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_moyen_paiement(row))
        delete_action.triggered.connect(lambda: self.delete_selected_moyen_paiement(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.moyen_paiement_table.viewport().mapToGlobal(pos))

    def show_context_menu_type_tier(self, pos: QPoint):
        item = self.type_tier_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_type_tier(row))
        delete_action.triggered.connect(lambda: self.delete_selected_type_tier(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.type_tier_table.viewport().mapToGlobal(pos))

    def show_context_menu_operation(self, pos: QPoint):
        item = self.transaction_table.itemAt(pos)
        if not item or self.pointage_state["actif"] :
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)
        dupliquer_action = QAction("Dupliquer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_operation(row,True))
        delete_action.triggered.connect(lambda: self.delete_selected_operation(row))
        dupliquer_action.triggered.connect(lambda: self.edit_selected_operation(row,False))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(dupliquer_action)
        
        menu.exec(self.transaction_table.viewport().mapToGlobal(pos))

    def show_context_menu_historique_placement(self, pos: QPoint):
        item = self.history_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)
        
        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)

        edit_action.triggered.connect(lambda: self.edit_selected_historique_placement(row))
        delete_action.triggered.connect(lambda: self.delete_selected_historique_placement(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        menu.exec(self.history_table.viewport().mapToGlobal(pos))

    def apply_filters(self):
        if self.current_account is None:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte d'abord.")
            return
        selected_categories = set(self.categorie_filter.checkedItems())
        selected_sous_categories = set(self.sous_categorie_filter.checkedItems())
        selected_tiers = [
            self.tiers_nom_to_id[nom]
            for nom in self.tiers_filter.checkedItems()
            if nom in self.tiers_nom_to_id
        ]

        selected_comptes= [self.current_account]
        for nom in self.compte_filter.checkedItems():
            if nom in self.comptes_nom_to_id:
                selected_comptes.append(self.comptes_nom_to_id[nom])

        date_debut = int(self.date_debut_filter.date().toString("yyyyMMdd"))
        date_fin = int(self.date_fin_filter.date().toString("yyyyMMdd"))
        state = self.bq_filter.checkState()
        if state == Qt.CheckState.Checked:
            # filtrer uniquement les opérations pointées
            bq = True
        elif state == Qt.CheckState.Unchecked:
            # filtrer uniquement les opérations non pointées
            bq = False
        else:
            # état PartiallyChecked = ne pas filtrer sur ce critère
            bq = None

        self.load_operations(GetFilteredOperations(date_debut,date_fin,selected_categories,selected_sous_categories,selected_tiers,selected_comptes,bq),0)
        self.transaction_table.setColumnHidden(15,True)
            
    def reset_filters(self):
        # Vider les sélections
        self.categorie_filter.clear()
        self.sous_categorie_filter.clear()
        self.tiers_filter.clear()
        for cat in GetCategorie():
            self.categorie_filter.addItem(cat.nom)
            for sous_cat in GetSousCategorie(cat.nom):
                self.sous_categorie_filter.addItem(sous_cat.nom)    
        for tier in GetTiers():
            self.tiers_filter.addItem(tier.nom)

        self.load_operations()
        self.transaction_table.setColumnHidden(16,False)
        

        # Réinitialiser les dates
        from PyQt6.QtCore import QDate
        today = QDate.currentDate()
        self.date_debut_filter.setDate(today.addMonths(-1))
        self.date_fin_filter.setDate(today)

        # Réafficher toutes les lignes
        for row in range(self.transaction_table.rowCount()):
            self.transaction_table.setRowHidden(row, False)

    def commencer_pointage(self):
        if not self.current_account:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte.")
            return

        solde, date = GetDerniereValeurPointe(self.current_account)  # à créer dans GestionBD
        result = show_pointage_dialog(self, solde, str(date))

        if result:
            self.pointage_state['actif'] = True
            self.pointage_state['somme_pointees'] = 0
            self.pointage_state['solde'] = result['solde']
            self.pointage_state['date'] = result['date']
            self.pointage_state['solde'] = solde  # point de départ
            self.pointage_state['target'] = result['solde']   # objectif à atteindre

            self.pointage_info_label.setText(
                f"Dernier relevé : {result['solde']:.2f} €"
            )
            self.pointage_info_label.show()
            self.pointage_btn.hide()
            self.cancel_pointage_btn.show()
            self.end_pointage_btn.show()
            self.suspendre_pointage_btn.show()
            self.add_transaction_btn.setEnabled(False)

    def suspendre_pointage(self):
        self.pointage_state['suspendu'] = True
        self.pointage_info_label.setText("⏸️ Pointage suspendu")
        self.pointage_info_label.show()
        self.reprendre_pointage_btn.show()
        self.suspendre_pointage_btn.hide()
        self.pointage_btn.hide()
        self.end_pointage_btn.show()
        self.cancel_pointage_btn.show()
        self.add_transaction_btn.setEnabled(True)        
          

    def handle_table_click(self, row, column):
        handle_bq_click(row, column, self.transaction_table, self.pointage_state, self, self)

    def reprendre_pointage(self):
        if not self.pointage_state.get('suspendu', False):
            QMessageBox.information(self, "Reprise impossible", "Aucun pointage suspendu à reprendre.")
            return

        self.pointage_state['actif'] = True
        self.pointage_state['suspendu'] = False

        # Récupérer toutes les opérations de nouveau
        operations = GetOperationsNotBq(self.current_account)
        solde_depart = GetDerniereValeurPointe(self.current_account)[0]

        # Recharger le tableau depuis le solde de départ
        self.transaction_table.setRowCount(0)
        self._populate_transaction_table(operations, solde_depart)

        # Réappliquer les styles sur les lignes déjà pointées
        for row in self.pointage_state['rows']:
            self.transaction_table.selectRow(row)
            self.transaction_table.item(row, 9).setText("P")  # Colonne Bq

        # UI
        self.pointage_info_label.setText(f"Dernier relevé : {self.pointage_state['target']:.2f} € – Somme pointées : {self.pointage_state['somme_pointees']:.2f} € – Écart : {round(self.pointage_state['target'] - self.pointage_state['solde'],2):.2f} €")
        self.pointage_info_label.show()
        self.reprendre_pointage_btn.hide()
        self.suspendre_pointage_btn.show()
        self.end_pointage_btn.show()
        self.cancel_pointage_btn.show()
        self.pointage_btn.hide()

    def terminer_pointage(self):
        finalize_pointage(self.pointage_state, self.pointage_state['target'],self.pointage_state['date'],self)
        self.pointage_info_label.hide()
        self.suspendre_pointage_btn.hide()
        self.end_pointage_btn.hide()
        self.cancel_pointage_btn.hide()
        self.pointage_btn.show()
        self.add_transaction_btn.setEnabled(True)
        self.load_operations()

    def annuler_pointage(self):
        cancel_pointage(self.pointage_state,self.transaction_table)
        self.pointage_info_label.hide()
        self.cancel_pointage_btn.hide()
        self.end_pointage_btn.hide()
        self.suspendre_pointage_btn.hide()
        self.reprendre_pointage_btn.hide()
        self.pointage_btn.show()
        self.add_transaction_btn.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        * {
            font-size: 18px;
        }
    """)
    window = MoneyManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
