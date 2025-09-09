import sys

from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QListWidgetItem, QMessageBox,
    QAbstractItemView, QTabWidget,QMenu,QStackedLayout,QGridLayout,QSpacerItem,QSizePolicy,QFileDialog,QGroupBox
)
from views.dialogs.ShowPointageDialog import show_pointage_dialog, handle_bq_click, finalize_pointage,cancel_pointage
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QAction,QColor,QCursor,QIcon,QFont
from PyQt6.QtCore import Qt, QPoint, QUrl, QObject, pyqtSlot, pyqtSignal,QSettings,QStandardPaths
from database.gestion_bd import *
from utils.CheckableComboBox import *
from utils.DateTableWidgetItem import *
from views.dialogs.ImportDialog import *
from utils.ImportQIF import *
from views.dialogs.AddEditLoanDialog import *
from views.dialogs.AddEditEcheanceDialog import *
from views.dialogs.AddEditAccountDialog import *
from views.dialogs.AddEditOperationDialog import *
from views.dialogs.AddEditTypeBeneficiaireDialog import *
from views.dialogs.AddEditBeneficiaireDialog import *
from views.dialogs.AddEditPositionDialog import *
from views.dialogs.AddEditTierDialog import *
from views.dialogs.AddEditPlacementDialog import *
from views.dialogs.ReplaceTierDialog import *
from views.dialogs.ReplaceSousCategorieDialog import *
from views.dialogs.ReplaceCategorieDialog import *
from views.dialogs.ReplaceTypeTierDialog import *
from views.dialogs.ReplaceMoyenPaiementDialog import *
from views.dialogs.AddEditSousCategorieDialog import *
from views.dialogs.AddEditCategorieDialog import *
from views.dialogs.AddEditTypeTierDialog import *
from views.dialogs.AddEditMoyenPaiementDialog import *
from views.dialogs.ShowPerformanceDialog import *
from typing import Optional
from PyQt6.QtWebEngineWidgets import QWebEngineView
from models import TypeOperation,TypePosition
from utils.GetPlacementValue import GetLastValuePlacement
import plotly.graph_objects as go
import plotly.graph_objs as go
import json
import plotly
import os
import datetime
from utils.HTMLJSTemplate import generate_html_with_js
from utils.ComputeLoan import *


class ClickHandler(QObject):
    clicked =   pyqtSignal(dict,bool)  # Signal to propagate data

    @pyqtSlot(str)
    def handle_click(self, data_json_str):
        import json
        data = json.loads(data_json_str)
        self.clicked.emit(data, data["last_ring"])

def sunburst_chart(data_raw, hierarchy_columns,title, value_column="montant", color_column=None, root_name="Balance", negative_value_treatment=None):
    """
    Generates a Sunburst chart from raw data with a customizable hierarchy.
    Handles negative values by categorizing them (e.g., as "Dépenses") and converting to absolute
    for visualization, while displaying the true (signed) total balance in the root's label.

    Args:
        data_raw (list of dict): The input data, where each dictionary represents a row.
                                  Expected to have 'montant' and other columns specified in hierarchy_columns.
        hierarchy_columns (list of str): A list of column names defining the hierarchy
                                         from the outermost ring to the innermost.
                                         Example: ["type_flux", "compte", "categorie", "sous_cat"]
        value_column (str): The name of the column containing the numerical values for aggregation.
                            Defaults to "montant".
        color_column (str, optional): The name of the column to use for coloring the top-level segments.
                                      If None, default colors (red/green for negative/positive) are used.
                                      If specified, all segments will use the same color.
        root_name (str): The label for the center of the sunburst chart. Defaults to "Total".
        negative_value_treatment (dict, optional): A dictionary specifying how to handle negative values.
                                                   Expected keys:
                                                       "column_to_update": (str) The column whose value should be updated (e.g., "type_flux").
                                                       "negative_label": (str) The label to assign if the original value is negative.
                                                       "positive_label": (str) The label to assign if the original value is positive.
                                                   If None, negative values are treated as a default 'Dépenses' type.
                                                   Example: {"column_to_update": "type_flux", "negative_label": "Dépenses", "positive_label": "Revenus"}
    Returns:
        plotly.graph_objects.Figure: A Plotly Sunburst chart figure.
    """

    processed_data = []
    compte_ids = []
    tiers_ids = []
    beneficiaires_ids = []
    true_total_balance = round(sum(entry[value_column] for entry in data_raw), 2) # Keep true balance for root label

    for entry in data_raw:
        new_entry = entry.copy()
        # Handle negative values: assign label, and CONVERT TO ABSOLUTE for chart size
        if negative_value_treatment:
            if new_entry[value_column] < 0:
                new_entry[negative_value_treatment["column_to_update"]] = negative_value_treatment["negative_label"]
                new_entry[value_column] = round(abs(new_entry[value_column]), 2) # CONVERT TO ABSOLUTE
            else:
                new_entry[negative_value_treatment["column_to_update"]] = negative_value_treatment["positive_label"]
                new_entry[value_column] = round(new_entry[value_column], 2) # Keep as is, already positive
        else: # Default behavior if no specific treatment is provided
            if new_entry[value_column] < 0:
                new_entry["type_flux"] = "Dépenses"
                new_entry[value_column] = round(abs(new_entry[value_column]), 2) # CONVERT TO ABSOLUTE
            else:
                new_entry["type_flux"] = "Revenus"
                new_entry[value_column] = round(new_entry[value_column], 2) # Keep as is, already positive

        processed_data.append(new_entry)
        if "compte_id" in new_entry:
            compte_ids.append(new_entry["compte_id"])
        else:
            compte_ids.append(None)
        
        if "tiers_id" in new_entry:
            tiers_ids.append(new_entry["tiers_id"])
        else:
            tiers_ids.append(None)
        
        if "beneficiaire" in new_entry:
            beneficiaires_ids.append(new_entry["beneficiaire"])
        else:
            beneficiaires_ids.append(None)

    # --- Construction des listes pour le Sunburst ---
    sunburst_labels = []
    sunburst_parents = []
    sunburst_values = [] # These will always be positive values for chart size
    sunburst_ids = []
    sunburst_colors = []

    # Dictionnaire pour agréger les totaux par ID unique (now summing absolute values)
    aggregated_totals = {}
    added_ids_to_sunburst_lists = set()

    # Define colors
    COLOR_DEFAULT_NEGATIVE = 'rgb(200, 50, 50)'   # Tomato (red)
    COLOR_DEFAULT_POSITIVE = 'rgb(0, 204, 136)'  # Medium Green
    COLOR_ROOT_POSITIVE = 'rgb(0, 140, 0)'      # Forest Green
    COLOR_ROOT_NEGATIVE = 'rgb(160, 40, 40)'      # Indian Red
    COLOR_ROOT_ZERO = 'rgb(100, 100, 100)'        # Gray for zero balance - inchangé

    # IDS Splitter
    var_split = "##"

    # Step 1: Process leaf nodes and accumulate totals for all levels
    for entry in processed_data:
        current_path_components = []
        parent_id = ""
        current_id = ""
        # Montant is already absolute from preprocessing for chart sizing
        montant = entry[value_column]

        for i, col in enumerate(hierarchy_columns):
            component = str(entry[col])
            current_path_components.append(component)
            current_id = var_split.join(current_path_components)

            # Aggregate absolute values
            aggregated_totals[current_id] = aggregated_totals.get(current_id, 0) + montant

            if i == len(hierarchy_columns) - 1:  # This is the leaf node
                if current_id not in added_ids_to_sunburst_lists:
                    sunburst_ids.append(current_id)
                    # For leaf nodes, display the absolute value in label
                    sunburst_labels.append(f"{component} ({montant}€)")
                    sunburst_parents.append(parent_id if parent_id else root_name)
                    sunburst_values.append(montant) # Append the absolute amount

                    # Determine color based on original classification (Dépenses/Revenus)
                    if color_column and color_column in entry:
                        sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if entry[color_column] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                    elif negative_value_treatment and negative_value_treatment["column_to_update"] in entry:
                         sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if entry[negative_value_treatment["column_to_update"]] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                    else:
                        if "type_flux" in new_entry:
                            sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if new_entry["type_flux"] == "Dépenses" else COLOR_DEFAULT_POSITIVE)
                        else:
                            sunburst_colors.append(COLOR_DEFAULT_POSITIVE)

                    added_ids_to_sunburst_lists.add(current_id)

            parent_id = current_id

    # Step 2: Add intermediate and root nodes
    for i in range(len(hierarchy_columns) - 1, -1, -1):
        col = hierarchy_columns[i]
        unique_combinations = set()

        for entry in processed_data:
            current_path_components = []
            for j in range(i + 1):
                current_path_components.append(str(entry[hierarchy_columns[j]]))
            unique_combinations.add(tuple(current_path_components))

        for combo in unique_combinations:
            current_id = var_split.join(combo)

            if current_id not in added_ids_to_sunburst_lists:
                sunburst_ids.append(current_id)
                sunburst_labels.append(combo[-1])

                parent_id = ""
                if len(combo) > 1:
                    parent_id = var_split.join(combo[:-1])
                else:
                    parent_id = root_name # Top-level items parent to the root

                sunburst_parents.append(parent_id)
                sunburst_values.append(aggregated_totals.get(current_id, 0)) # Aggregate absolute values

                # Determine color based on top-level category
                if color_column and color_column in processed_data[0]:
                    original_entry_for_color = next((item for item in processed_data if var_split.join([str(item[c]) for c in hierarchy_columns[:len(combo)]]) == current_id), None)
                    if original_entry_for_color:
                        sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if original_entry_for_color[color_column] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                    else:
                        sunburst_colors.append(COLOR_DEFAULT_POSITIVE)
                elif negative_value_treatment and negative_value_treatment["column_to_update"] in processed_data[0]:
                     original_entry_for_color = next((item for item in processed_data if var_split.join([str(item[c]) for c in hierarchy_columns[:len(combo)]]) == current_id), None)
                     if original_entry_for_color:
                         sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if original_entry_for_color[negative_value_treatment["column_to_update"]] == negative_value_treatment["negative_label"] else COLOR_DEFAULT_POSITIVE)
                     else:
                         sunburst_colors.append(COLOR_DEFAULT_POSITIVE)
                else:
                    first_level_category = combo[0]
                    sunburst_colors.append(COLOR_DEFAULT_NEGATIVE if first_level_category == "Dépenses" else COLOR_DEFAULT_POSITIVE)

                added_ids_to_sunburst_lists.add(current_id)

    # --- Add the ROOT node ---
    root_label_text = ""
    root_color_final = ''
    if true_total_balance < 0:
        root_label_text = f"{root_name} (Déficit: {abs(round(true_total_balance, 2))}€)"
        root_color_final = COLOR_ROOT_NEGATIVE
    elif true_total_balance > 0:
        root_label_text = f"{root_name} (Surplus: {round(true_total_balance, 2)}€)"
        root_color_final = COLOR_ROOT_POSITIVE
    else:
        root_label_text = f"{root_name} (Equilibre: 0€)"
        root_color_final = COLOR_ROOT_ZERO

    sum_of_top_level_abs_values = 0
    if hierarchy_columns:
        first_level_col = hierarchy_columns[0]
        for entry in processed_data:
            sum_of_top_level_abs_values += round(entry[value_column], 2) 

    if root_name not in added_ids_to_sunburst_lists:
        sunburst_ids.append(root_name)
        sunburst_labels.append(root_label_text)
        sunburst_parents.append("")
        sunburst_values.append(sum_of_top_level_abs_values) 
        sunburst_colors.append(root_color_final)
        added_ids_to_sunburst_lists.add(root_name)

    last_ring = max(len(y.split(var_split)) for y in sunburst_ids)
    last_ring_values = [False] * len(sunburst_ids)
    for index, sunburst_id in enumerate(sunburst_ids):
        if len(sunburst_id.split(var_split)) == last_ring:
            last_ring_values[index] = True

    custom_data = list(zip(last_ring_values, compte_ids,tiers_ids))

    # --- Création du graphique Sunburst ---
    fig = go.Figure(go.Sunburst(
        ids=sunburst_ids,
        labels=sunburst_labels,
        parents=sunburst_parents,
        values=sunburst_values,
        branchvalues='total',
        insidetextfont=dict(color="white", size=16),  # texte au centre des secteurs
        outsidetextfont=dict(color="white", size=14),  # texte à l'extérieur
        customdata=custom_data,
        marker=dict(colors=sunburst_colors)
    ))

    fig.update_layout(
        title=title, # Generic title
        height=1200,
        width=1200,
        margin=dict(t=30, l=0, r=0, b=0),
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        font=dict(color="#ffffff")
    )

    return fig

def table_style(table:QTableWidget):
    table.setStyleSheet("""
            QHeaderView::section{
                border: 1px solid white;
                padding: 4px;
                font-weight: bold;}
            QTableWidget::item{
                padding-left: 6px;
                padding-right: 6px;}""")


def align(item: QTableWidgetItem,alignement:Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> QTableWidgetItem:
    item.setTextAlignment(alignement)
    return item
    

def format_montant(montant,is_nb_part = 0):
    if is_nb_part:
        return f"{float(montant):,.4f}".replace(",", " ").replace(".", ",") + " €" if montant != 0 else ""
    else:   
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

    def create_new_db_dialog(self):
        """Ouvre un dialogue pour créer un nouveau fichier .db."""
        # Propose un répertoire par défaut, par exemple le répertoire des documents de l'utilisateur
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        
        # Propose un nom de fichier par défaut
        default_filename = os.path.join(default_dir, "nouvelle_base.db")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Créer une nouvelle base de données",
            default_filename,
            "Fichiers de base de données SQLite (*.db);;Tous les fichiers (*.*)"
        )

        if file_path:
            # S'assurer que l'extension .db est présente
            if not file_path.lower().endswith(".db"):
                file_path += ".db"
            
            # Tenter de créer un fichier vide pour s'assurer du chemin valide
            try:
                # Créer le fichier vide (sqlite3.connect le fera aussi, mais c'est une vérif explicite)
                open(file_path, 'a').close() 
                self.set_current_db(file_path, is_new=True)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur de création de fichier",
                    f"Impossible de créer le fichier à cet emplacement : {e}"
                )
                print(f"Erreur de création de fichier: {e}")
        else:
            QMessageBox.information(
                self,
                "Opération annulée",
                "Création de la nouvelle base de données annulée."
            )
            print("Création de la nouvelle DB annulée.")
    def run_echeance_if_db_ready(self):
        """Exécute RunEcheance seulement si une DB est active."""
        if self.current_db_path:
            try:
                echeances = GetEcheanceToday(db_path=self.current_db_path)
                RunEcheance(echeances, db_path=self.current_db_path)
                liste_compte_pret = GetComptePret()
                for compte_id in liste_compte_pret:
                    new_solde,date, = GetCRD(compte_id,self.current_db_path)
                    if new_solde is not None:
                        UpdateSoldeCompte(compte_id,new_solde)
                        if new_solde == 0:
                            DeleteEcheancePret(compte_id)
                self.echeance_table.clearContents()
                self.load_echeance()
                self.account_list.clear()
                self.load_accounts()
            except Exception as e:
                print(f"Erreur lors du traitement des échéances : {e}")
                # Vous pourriez afficher un QMessageBox ici si l'erreur est critique

    def initialize_db_on_startup(self):
        """Gère la logique d'initialisation de la DB au démarrage de l'application."""
        if self.current_db_path:
            # Tente de se connecter et d'initialiser les tables pour la DB chargée
            try:
                create_tables(self.current_db_path)
                self.run_echeance_if_db_ready() # Exécute RunEcheance seulement si la DB est prête
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur de chargement DB",
                    f"Impossible de charger la base de données '{os.path.basename(self.current_db_path)}' : {e}\n"
                    "Veuillez sélectionner ou créer une nouvelle base de données."
                )
                print(f"Erreur de chargement DB : {e}")
                self.current_db_path = None # Réinitialiser le chemin si échec
                self.settings.remove("last_db_path") # Supprimer le chemin invalide

        self.update_ui_for_db_status()

    def update_ui_for_db_status(self):
        # Cette fonction peut être appelée pour ajuster l'interface utilisateur
        # en fonction de si une DB est chargée ou non.
        if self.current_db_path:
            self.setWindowTitle(f"Money - [{os.path.basename(self.current_db_path)}]")
            # Vous pourriez activer/désactiver certains boutons ici
            # self.test_button.setEnabled(True)
        else:
            self.setWindowTitle("Money - [Aucune base de données chargée]")
            # self.test_button.setEnabled(False)

    def load_last_db_path(self):
        """Charge le chemin de la dernière DB utilisée depuis les paramètres."""
        last_path = self.settings.value("last_db_path", "")
        if last_path and os.path.exists(last_path):
            self.current_db_path = last_path
        else:
            print("Aucune dernière DB valide trouvée ou le fichier n'existe pas.")
    def save_last_db_path(self, path):
        """Sauvegarde le chemin de la DB actuelle dans les paramètres."""
        self.settings.setValue("last_db_path", path)

    def update_value_placement(self):
        try:
            tickers = GetTickerPlacement()  # Liste des tickers sous forme [(id_placement, ticker), ...]

            # Récupération groupée des dernières valeurs
            for id_placement, ticker_symbol in tickers:
                last_values = GetLastValuePlacement(ticker_symbol)  # Doit retourner un dict : {ticker: (date, value)}                
                # Si la valeur du ticker est bien récupérée
                if ticker_symbol in last_values:
                    date, value = last_values[ticker_symbol]
                    type_placement = GetTypePlacement(id_placement)

                    historique = HistoriquePlacement(
                        id_placement, type_placement, date, value,
                        "Actualisation automatique", ticker_symbol
                    )

                    # Tentative d'insertion unique
                    if not InsertHistoriquePlacement(historique):
                        DeleteHistoriquePlacement(id_placement, date)
                        InsertHistoriquePlacement(historique)

            # Rafraîchissement des vues
            self.placement_table.clearContents()
            self.load_placement()
            self.account_list.clear()
            self.load_accounts()

        except Exception as e:
            print(f"Erreur dans update_value_placement: {e}")


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Money")
        # Initialisation pour l'audio (s'assurer que QAudioOutput et QMediaPlayer sont importés de QtMultimedia)
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output) # Associer la sortie audio au lecteur
        icon_path = "Finao.ico"
        self.setWindowIcon(QIcon(icon_path))

        # Initialisation des états de la DB
        self.current_db_path = None
        self.categorie_clicked = None
        self.type_benficiaire_clicked = None
        self.type_tier_clicked = None
        self.current_account_label = None
        self.current_account = None # Gardez ceci si vous l'utilisez pour l'état de l'application
        self.pointage_state = {'actif': False, 'solde': 0.0, 'date': '','ops' : set(),'rows' : set(),'suspendu': False}

        self.settings = QSettings("Langello Corp", "Money") # Remplacez par le nom de votre organisation/app

        # Tenter de charger la dernière DB utilisée
        self.load_last_db_path()

        # Configurer l'interface utilisateur
        if self.current_db_path is not None:
            self.setup_ui()

            # Gérer la logique de démarrage de la DB
            self.initialize_db_on_startup()
            self.update_value_placement()
            
        else:
            menu_bar = self.menuBar()
            file_menu = menu_bar.addMenu("Fichier")

            exit_action = QAction("Quitter", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            open_action = QAction("Ouvrir", self)
            open_action.triggered.connect(self.open_db)
            file_menu.addAction(open_action)

            new_db_action = QAction("Nouveau", self)
            new_db_action.triggered.connect(self.new_db)
            file_menu.addAction(new_db_action)

            import_qif_action = QAction("Importer", self)
            import_qif_action.triggered.connect(self.import_qif)
            file_menu.addAction(import_qif_action)

        self.showMaximized()
           
    def setup_ui(self):
        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Fichier")
        help_menu = menu_bar.addMenu("Aide")

        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        open_action = QAction("Ouvrir", self)
        open_action.triggered.connect(self.open_db)
        file_menu.addAction(open_action)

        new_db_action = QAction("Nouveau", self)
        new_db_action.triggered.connect(self.new_db)
        file_menu.addAction(new_db_action)

        import_qif_action = QAction("Importer", self)
        import_qif_action.triggered.connect(self.import_qif)
        file_menu.addAction(import_qif_action)

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

        self.moyen_paiement_tab = QWidget()
        self.tabs.addTab(self.moyen_paiement_tab, "Gestion des moyens de paiement")
        self.setup_moyen_paiement_tab()

        self.echeancier_tab = QWidget()
        self.tabs.addTab(self.echeancier_tab, "Gestion de l'échéancier")
        self.setup_echeancier_tab()

        self.etat_tab = QWidget()
        self.tabs.addTab(self.etat_tab, "Etat")

        self.setup_etat_tab()

    def apply_filters_etat(self):
        self.update_etat_graph()

    def update_etat_graph(self):
        date_debut = int(self.date_debut_filter_etat.date().toString("yyyyMMdd"))
        date_fin = int(self.date_fin_filter_etat.date().toString("yyyyMMdd"))
        choix = self.etat_combobox.currentText()
        if choix == "Bilan Période par catégorie":
            data_raw,hierarchy_level,negative_value_treatment = GetBilanByCategorie(date_debut,date_fin)
            fig = sunburst_chart(data_raw,hierarchy_level,choix,negative_value_treatment=negative_value_treatment)

        elif choix == "Bilan Période par tiers":
            data_raw,hierarchy_level,negative_value_treatment = GetBilanByTiers(date_debut,date_fin)
            fig = sunburst_chart(data_raw,hierarchy_level,choix,negative_value_treatment=negative_value_treatment)

        elif choix == "Bilan Période par bénéficiaire":
            data_raw,hierarchy_level,negative_value_treatment = GetBilanByBeneficiaire(date_debut,date_fin)
            fig = sunburst_chart(data_raw,hierarchy_level,choix,negative_value_treatment=negative_value_treatment)
        # 1. Générez le div Plotly
        plotly_div = plotly.offline.plot(fig, include_plotlyjs='cdn', output_type='div')
        html_with_js = generate_html_with_js(plotly_div)
        self.etat_chart.setHtml(html_with_js)

    def setup_etat_tab(self):
        layout = QVBoxLayout(self.etat_tab)
        filter_layout = QHBoxLayout(self.etat_tab)

        self.date_debut_filter_etat = CustomDateEdit()
        self.date_debut_filter_etat.setDate(QDate(QDate.currentDate().year(), 1, 1))  # Par défaut, 1 mois avant

        self.date_fin_filter_etat = CustomDateEdit()
        self.date_fin_filter_etat.setDate(QDate.currentDate())  # Aujourd'hui

        self.apply_filters_etat_btn = QPushButton("Appliquer les filtres")
        self.reload_etat_btn = QPushButton("Recharger le graphique")

        # Combobox pour sélectionner l'analyse
        self.etat_combobox = QComboBox()
        self.etat_combobox.addItems(["Bilan Période par catégorie","Bilan Période par tiers","Bilan Période par bénéficiaire"])
        self.etat_combobox.currentIndexChanged.connect(self.update_etat_graph)
        filter_layout.addWidget(QLabel("Date début période: "))
        filter_layout.addWidget(self.date_debut_filter_etat)
        filter_layout.addSpacing(10) # Add 10 pixels of spacing
        filter_layout.addWidget(QLabel("Date fin période: "))
        filter_layout.addWidget(self.date_fin_filter_etat)
        filter_layout.addSpacing(10) # Still good to add a stretch at the end
        filter_layout.addWidget(self.apply_filters_etat_btn)
        filter_layout.addSpacing(10)
        filter_layout.addWidget(self.reload_etat_btn)
        filter_layout.addStretch(1)

        self.apply_filters_etat_btn.clicked.connect(self.apply_filters_etat)
        self.reload_etat_btn.clicked.connect(self.apply_filters_etat)

        layout.addLayout(filter_layout)
        layout.addWidget(self.etat_combobox)

        # Zone de graphique Plotly
        self.etat_chart = QWebEngineView()
        self.channel = QWebChannel()
        self.click_handler = ClickHandler()
        self.channel.registerObject('handler', self.click_handler)
        self.etat_chart.page().setWebChannel(self.channel)
        self.click_handler.clicked.connect(self.process_click_data)

        layout.addWidget(self.etat_chart)


        # Initialiser avec un graphique vide ou le 1er affichage
        self.update_etat_graph()

    def process_click_data(self, data, is_last_ring):
        date_debut = int(self.date_debut_filter_etat.date().toString("yyyyMMdd"))
        date_fin = int(self.date_fin_filter_etat.date().toString("yyyyMMdd"))
        if is_last_ring: # Nouvelle condition
            self.table_stack.setCurrentIndex(0)
            self.transaction_table.clearContents()
            self.position_table.clearContents()
            if self.etat_combobox.currentText() == "Bilan Période par catégorie":
                self.load_operations(GetFilteredOperations(date_debut=date_debut,date_fin=date_fin,categories=[data["id"].split("##")[2]],sous_categories=[data["id"].split("##")[3]],comptes=[data["compte_id"]]),0)          
            elif self.etat_combobox.currentText() == "Bilan Période par tiers":
                self.load_operations(GetFilteredOperations(date_debut=date_debut,date_fin=date_fin,tiers=[data["tiers_id"]],comptes=[data["compte_id"]]),0)
            elif self.etat_combobox.currentText() == "Bilan Période par bénéficiaire":
                self.load_operations(GetFilteredOperations(date_debut=date_debut,date_fin=date_fin,beneficiaires=[data["id"].split("##")[3]],comptes=[data["compte_id"]]),0)
            self.tabs.setCurrentWidget(self.operation_tab)
            self.transaction_table.setColumnHidden(16,True)
            self.pointage_btn.setEnabled(False)
            self.add_transaction_btn.setEnabled(False)

    def setup_echeancier_tab(self):
        layout = QVBoxLayout(self.echeancier_tab)

        self.echeance_table = QTableWidget(0, 20)
        self.echeance_table.setHorizontalHeaderLabels(["Fréquence", "1 ère\néchéance", "Prochaine\néchéance", "Compte", "Type\nopération", "Compte\nassocié", "Type\nde\ntiers", "Tiers\nPlacement",
                                                       "Catégorie","Sous-\nCatégorie","Moyen\nde\npaiement","Type\nbénéficiaire","Bénéficiaire","Débit","Crédit","Nb parts","Val part","Frais","Intérêts","Notes"])
        self.echeance_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_style(self.echeance_table)
        self.echeance_table.resizeColumnsToContents()
        self.echeance_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.echeance_table.customContextMenuRequested.connect(self.show_context_menu_echeancier)
        self.echeance_table.setAlternatingRowColors(True)
        self.echeance_table.setSortingEnabled(True)

        generer_btn = QPushButton("Ajouter une échéance")
        generer_btn.clicked.connect(self.add_echeance)

        layout.addWidget(self.echeance_table)
        layout.addWidget(generer_btn)

        self.load_echeance()

    def add_echeance(self):
        dialog = EcheanceDialog(GetComptesHorsPret(), self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            compte_choisi_id = dialog.get_selected_compte_id()
            if compte_choisi_id is not None:
                type = GetCompteType(compte_choisi_id)      
                if type in ["Courant","Epargne"]:
                    self.open_add_operation_dialog(isEcheance=True, echeance=None, compte_choisi_id = compte_choisi_id)
                else:
                    self.open_add_position_dialog(isEcheance=True, echeance=None,compte_choisi_id = compte_choisi_id)



    def load_accounts(self):
        for compte in GetComptes(self.current_db_path):
            self.add_account_to_list(compte)
        self.add_total_to_list()  # Ajoute le total à la fin

    def load_tiers(self,tiers = None):
        self.tier_table.setSortingEnabled(False)
        self.tier_table.setRowCount(0)
        if tiers is None:
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

    def load_pret(self):
        self.pret_table.setRowCount(0)
        for echeance in GetPret(self.current_account):
            self.add_pret_row(echeance)
        self.pret_table.sortItems(0,Qt.SortOrder.AscendingOrder)

    def load_sous_categories(self,sous_categories = None):
        self.sous_categorie_table.setSortingEnabled(False)
        if sous_categories is None:
            sous_categories = GetAllSousCategorie()
        self.sous_categorie_table.setRowCount(len(sous_categories))

        for row, sous_cat in enumerate(sous_categories):
            self.add_sous_categorie_row(row, sous_cat)

        self.sous_categorie_table.resizeColumnsToContents()
        self.sous_categorie_table.setSortingEnabled(True)
        self.sous_categorie_table.sortItems(1,Qt.SortOrder.AscendingOrder)

    def load_beneficiaire(self,beneficiaires = None):
        self.sous_categorie2_table.setSortingEnabled(False)
        if beneficiaires is None:
            beneficiaires = GetAllBeneficiaire()
        self.sous_categorie2_table.setRowCount(len(beneficiaires))

        for row, beneficiaire in enumerate(beneficiaires):
            self.add_beneficiaire_row(row, beneficiaire)

        self.sous_categorie2_table.resizeColumnsToContents()
        self.sous_categorie2_table.setSortingEnabled(True)
        self.sous_categorie2_table.sortItems(0,Qt.SortOrder.AscendingOrder)

    def load_placement(self):
        self.placement_table.setSortingEnabled(False)
        placements = GetLastPlacement()
        self.placement_table.setRowCount(len(placements))

        for row, placement in enumerate(placements):
            self.add_placement_row(row, placement)

        self.placement_table.resizeColumnsToContents()
        self.placement_table.setSortingEnabled(True)

    def load_echeance(self):
        self.echeance_table.setSortingEnabled(False)
        echeances = GetAllEcheance()
        self.echeance_table.setRowCount(len(echeances))

        for row, echeance in enumerate(echeances):
            self.add_echeance_row(row, echeance)

        self.echeance_table.resizeColumnsToContents()
        self.echeance_table.setSortingEnabled(True)

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
        if compte.solde >= 0:
            solde_label.setStyleSheet("color: #2ecc71;")
        else:
            solde_label.setStyleSheet("color: #e74c3c;")

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

    def on_categorie_clicked(self,item):
        self.load_sous_categories(GetSousCategorie(item.data(Qt.ItemDataRole.UserRole)))
        self.categorie_clicked = item.data(Qt.ItemDataRole.UserRole)
        self.sous_categorie_table.sortItems(0,Qt.SortOrder.AscendingOrder)

    def on_categorie2_clicked(self,item):
        self.load_beneficiaire(GetBeneficiairesByType(item.data(Qt.ItemDataRole.UserRole)))
        self.type_benficiaire_clicked = item.data(Qt.ItemDataRole.UserRole)
        self.sous_categorie2_table.sortItems(0,Qt.SortOrder.AscendingOrder)

    def on_type_tier_clicked(self,item):
        self.load_tiers(GetTiersByType(item.data(Qt.ItemDataRole.UserRole)))
        self.type_tier_clicked = item.data(Qt.ItemDataRole.UserRole)
        self.tier_table.sortItems(0,Qt.SortOrder.AscendingOrder)

    def on_account_clicked(self, item):

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            self.current_account = str(item.data(Qt.ItemDataRole.UserRole)["id"])
            selected_account = GetCompte(self.current_account)
            self.tabs.setCurrentWidget(self.operation_tab)
            self.add_transaction_btn.setEnabled(True)
            self.reset_filters()
            self.compte_filter.set_all_checked(False)
            self.compte_filter.checkItemByText(selected_account.nom)
            self.current_account_label.setVisible(True)
            font = QFont()
            self.current_account_label.setStyleSheet("""QLabel{border: 2px solid #007ACC;
                                                            padding: 5px;
                                                            border-radius: 5px;}""")
            self.current_account_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.current_account_label.adjustSize()
            font.setPointSize(16)
            font.setBold(True)
            self.current_account_label.setText(f"COMPTE : {selected_account.nom}")
            self.current_account_label.setFont(font)
            if not selected_account:
                return

            if selected_account.type == "Placement":
                self.table_stack.setCurrentIndex(1)
                self.filter_group_box.setVisible(False)
                self.apply_filter_btn_operation.hide()
                self.reset_filter_button_operation.hide()
                self.add_transaction_btn.setText("Ajouter une position")
                self.add_transaction_btn.clicked.disconnect()
                self.add_transaction_btn.clicked.connect(self.open_add_position_dialog)
                self.show_performance_btn.show()
                self.pointage_btn.hide()
                self.load_position()
            elif selected_account.type in ["Epargne", "Courant"]:
                self.table_stack.setCurrentIndex(0)
                self.filter_group_box.setVisible(True)
                self.apply_filter_btn_operation.show()
                self.reset_filter_button_operation.show()
                self.add_transaction_btn.setText("Ajouter une opération")
                self.add_transaction_btn.clicked.disconnect()
                self.add_transaction_btn.clicked.connect(self.open_add_operation_dialog)
                self.show_performance_btn.hide()
                self.pointage_btn.setText("Commencer le pointage")
                self.pointage_btn.clicked.disconnect()
                self.pointage_btn.clicked.connect(self.commencer_pointage)
                self.pointage_btn.show()
                self.load_operations()
            else:
                self.table_stack.setCurrentIndex(2)
                self.filter_group_box.setVisible(False)
                self.apply_filter_btn_operation.hide()
                self.reset_filter_button_operation.hide()
                self.pointage_btn.hide()
                self.show_performance_btn.hide()
                self.add_transaction_btn.setText("Ajouter un prêt")
                self.add_transaction_btn.clicked.disconnect()
                self.add_transaction_btn.clicked.connect(self.open_add_pret_dialog)                
                self.pointage_btn.setText("Modifier le prêt")
                self.pointage_btn.clicked.disconnect()
                self.pointage_btn.clicked.connect(self.open_edit_pret_dialog)
                self.pointage_btn.show()
                self.load_pret()

        except Exception as e:
            print("Erreur:", e)
            QMessageBox.warning(self, "Attention", "Le compte 'Total' n'est pas un compte valide, Veuillez choisir un autre compte.")

        finally:
            QApplication.restoreOverrideCursor()  # ⌛ restaure le curseur normal


    def open_add_account_dialog(self):
        dialog = AddEditAccountDialog(self)
        dialog.exec()

    def open_add_tier_dialog(self):
        if self.type_tier_clicked is not None:
            dialog = AddEditTierDialog(self,type_tier = self.type_tier_clicked)
        else:
            dialog = AddEditTierDialog(self)
        dialog.exec()

    def open_add_beneficiaire_dialog(self):
        if self.type_benficiaire_clicked is not None:
            dialog = AddEditBeneficiaireDialog(self,type_beneficiaire=self.type_benficiaire_clicked)
        else:
            dialog = AddEditBeneficiaireDialog(self)
        dialog.exec()

    def open_add_sous_categorie_dialog(self):
        if self.categorie_clicked is not None:
            dialog = AddEditSousCategorieDialog(self,categorie=self.categorie_clicked)
        else:
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
            self.load_operations()

    def edit_selected_placement(self, row):
        # Récupérer uniquement les informations nécessaires
        nom = self.placement_table.item(row, 0).text()
        placement = GetLastPlacementByName(nom)   

        # Ouvrir la boîte de dialogue en mode modification (seul le nom sera modifiable)
        dialog = AddEditPlacementDialog(self, placement=placement)
        if dialog.exec():
            # Mettre à jour uniquement la colonne du nom dans le tableau
            self.placement_table.item(row, 0).setText(dialog.nom.text())

    def actualiser_selected_placement(self, row):
        # Récupérer les infos du placement existant
        nom = self.placement_table.item(row, 0).text()
        placement = GetLastPlacementByName(nom)
        last_known_date = placement.date

        dialog = AddEditPlacementDialog(self, placement=placement, mode="actualiser")
        if dialog.exec():

            if int(dialog.date.date().toString("yyyyMMdd")) >= last_known_date:
                # Mise à jour complète de la ligne existante
                self.placement_table.item(row, 0).setText(dialog.nom.text())
                self.placement_table.item(row, 1).setText(dialog.ticker.text())
                self.placement_table.item(row, 2).setText(dialog.type.currentText())
                self.placement_table.item(row, 3).setText(datetime.datetime.strptime(str(dialog.new_placement.date), "%Y%m%d").strftime("%d/%m/%Y"))
                self.placement_table.item(row, 4).setText(format_montant(float(dialog.val_actualisee.text().replace(' ','')),1))
                self.placement_table.item(row, 5).setText("Actualisation")
        self.show_placement_history_graph(self.placement_table.item(row, 0))

    def voir_compte_selected_placement(self, row):
        item_nom = self.placement_table.item(row, 0)
        nom = item_nom.text()
        # Supposons que cette fonction retourne une liste
        resultats = GetComptePlacementNameByPlacement(nom)

        # Convertir la liste en texte lisible
        texte_popup = "\n".join(str(item) for item in resultats)

        # Créer et afficher une popup
        msg = QMessageBox(self)
        msg.setWindowTitle("Comptes associés au placement")
        msg.setText(f"Liste des comptes associés au placement '{nom}':")
        msg.setInformativeText(texte_popup)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

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

        # 🛑 Étape de confirmation : MODIFICATION ICI
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation de suppression")
        msg_box.setText(f"Êtes-vous sûr de vouloir supprimer le tiers '{tier.nom}' ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse

        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            autres_tiers = GetTiersActifByTypeExceptCurrent(type_tier, tier_id)
            if not autres_tiers:
                QMessageBox.warning(
                    self,
                    "Suppression impossible",
                    f"Aucun autre tiers de type '{type_tier}' disponible pour le remplacement."
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

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Suppression d'un compte")
        msg_box.setText(f"Toutes les opérations liées à ce compte vont être supprimées\nEtes-vous sûr de vouloir supprimer le compte ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé
        
        if reply_is_yes:
            item_nom = self.compte_table.item(row, 0)
            compte_id = str(item_nom.data(Qt.ItemDataRole.UserRole))
            DeleteCompte(compte_id)
            compte_type = GetCompteType(compte_id)
            if compte_type in ["Courant","Epargne"]:
                DeleteOperations(compte_id)
            if compte_type == "Prêt":
                DeletePret(compte_id)
            self.compte_table.removeRow(row)
            self.account_list.clear()
            self.transaction_table.clearContents()
            self.compte_table.clearContents()
            self.load_accounts()
            self.load_comptes()

    def delete_selected_operation(self, row):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Suppression d'une opération")
        msg_box.setText(f"L'opération va être définitivement supprimée\nEtes-vous sûr de vouloir supprimer l'opération ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé
        
        if reply_is_yes:
            item_nom = self.transaction_table.item(row, 0)
            operation_id = str(item_nom.data(Qt.ItemDataRole.UserRole))
            operation = GetOperation(operation_id)
            if operation.link:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Suppression d'une opération liée")
                msg_box.setText("L'opération est liée avec une autre.\nQuelles opérations voulez-vous supprimer ?")
                msg_box.setIcon(QMessageBox.Icon.Question)

                # Crée les boutons personnalisés
                bouton_oui = QPushButton("opération\nde ce\ncompte\n+\nopération liée")
                bouton_non = QPushButton("opération\nde ce\ncompte seule")
                bouton_annuler = QPushButton("Annuler")

                # Ajouter les boutons à la boîte
                msg_box.addButton(bouton_oui, QMessageBox.ButtonRole.YesRole)
                msg_box.addButton(bouton_non, QMessageBox.ButtonRole.NoRole)
                msg_box.addButton(bouton_annuler, QMessageBox.ButtonRole.RejectRole)
                msg_box.adjustSize()

                msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
                # Vérifier quel bouton a été cliqué
                clicked = msg_box.clickedButton()
                if clicked == bouton_oui:
                    reply_is_yes = True
                elif clicked == bouton_non:
                    reply_is_yes = False
                else:
                    reply_is_yes = None
                
                if reply_is_yes:
                    try:
                        o = GetOperation(operation.link)
                        DeleteOperation(o,o.credit,o.debit)
                    except:
                        p = GetPosition(operation.link)
                        DeletePosition(p)
            if reply_is_yes is not None:
                DeleteOperation(operation,operation.credit,operation.debit)
                self.transaction_table.removeRow(row)
                self.account_list.clear()
                self.transaction_table.clearContents()
                self.compte_table.clearContents()
                self.load_accounts()
                self.load_operations()
                self.load_comptes()

    def delete_selected_position(self, row):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Suppression d'une position")
        msg_box.setText(f"La position va être définitivement supprimée\nEtes-vous sûr de vouloir supprimer la position ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé
        
        if reply_is_yes:
            item_nom = self.position_table.item(row, 0)
            position_id = str(item_nom.data(Qt.ItemDataRole.UserRole))
            position = GetPosition(position_id)
            operation = GetLinkOperation(position_id)
            if operation:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Suppression d'une opération liée")
                msg_box.setText(f"La position est liée avec une autre opération, voulez-vous supprimer la position et l'opération ?")
                
                # Création et ajout des boutons "Oui" et "Non"
                bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
                bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
                
                msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

                msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
                # Vérifier quel bouton a été cliqué
                if msg_box.clickedButton() == bouton_oui:
                    reply_is_yes = True
                else:
                    reply_is_yes = False

                if not reply_is_yes:
                    return  # L'utilisateur a annulé
                
                if reply_is_yes:
                    DeleteOperation(operation,operation.credit,operation.debit)
                
            DeletePosition(position)
            self.position_table.removeRow(row)
            self.account_list.clear()
            self.position_table.clearContents()
            self.load_accounts()
            self.load_position()

    def delete_selected_placement(self, row):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Suppression du placement")
        msg_box.setText(f"Toutes les positions liés à ce placement vont être supprimées\nEtes-vous sûr de vouloir supprimer le placement ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé
        
        if reply_is_yes:
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
        beneficiaires = GetBeneficiairesByType(nom)
        if len(beneficiaires)> 0:
            QMessageBox.warning(self,"Suppresion du type de bénéficiaire impossible", "Impossible de supprimer le type de bénéficiaire, des bénéficiaires l'utilisent encore")
            return
        nb_operations_related = GetTypeBeneficiaireRelatedOperations(nom)
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation de suppression")
        msg_box.setText(f"Êtes-vous sûr de vouloir supprimer le type de bénéficiaire '{nom}' ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Suppression du type de bénéficiaire")
            msg_box.setText(f"{nb_operations_related} opération(s) utilisent ce type.\n"
                "Il sera remplacé par une valeur vide.\n"
                "Voulez-vous continuer ?")
            
            # Création et ajout des boutons "Oui" et "Non"
            bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
            bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
            
            msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

            msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
            # Vérifier quel bouton a été cliqué
            if msg_box.clickedButton() == bouton_oui:
                reply_is_yes = True
            else:
                reply_is_yes = False

            if not reply_is_yes:
                return 

            UpdateTypeBeneficiaireInOperations(nom, "")  # Remplace par chaîne vide

        DeleteTypeBeneficiaire(nom)  # Supprime le type de bénéficiaire
        self.load_type_beneficiaire()
        self.load_operations()


    def delete_selected_beneficiaire(self, row):
        item_nom = self.sous_categorie2_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole)["nom"])
        type_beneficiaire = str(item_nom.data(Qt.ItemDataRole.UserRole)["type_beneficiaire"])
        nb_operations_related = GetBeneficiaireRelatedOperations(nom)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation de suppression")
        msg_box.setText(f"Êtes-vous sûr de vouloir supprimer le bénéficiaire '{nom}'/'{type_beneficiaire}' ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Suppression du bénéficiaire")
            msg_box.setText(f"{nb_operations_related} opération(s) utilisent ce bénéficiaire.\n"
                "Elles seront remplacées par une valeur vide.\n"
                "Voulez-vous continuer ?")
            
            # Création et ajout des boutons "Oui" et "Non"
            bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
            bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
            
            msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

            msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
            # Vérifier quel bouton a été cliqué
            if msg_box.clickedButton() == bouton_oui:
                reply_is_yes = True
            else:
                reply_is_yes = False

            if not reply_is_yes:
                return 

            UpdateBeneficiaireInOperations(nom, "")  # Remplace par chaîne vide

        DeleteBeneficiaire(nom,type_beneficiaire)  # Supprime le type de bénéficiaire
        self.load_beneficiaire()
        self.load_operations()



    def delete_selected_sous_categorie(self, row):
        item_nom = self.sous_categorie_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole)["nom"])
        categorie_parent = str(item_nom.data(Qt.ItemDataRole.UserRole)["categorie_parent"])
        nb_operations_related = GetSousCategorieRelatedOperations(nom,categorie_parent)
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation de suppression")
        msg_box.setText(f"Êtes-vous sûr de vouloir supprimer la sous catégorie '{nom}' ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_sous_categorie = GetSousCategorieByCategorieParentExceptCurrent(nom, categorie_parent)

            if not autres_sous_categorie:
                # Aucun autre sous-catégorie dispo
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Suppression sous-catégorie")
                msg_box.setText("Aucune autre sous-catégorie disponible.\nVoulez-vous remplacer par une valeur vide ?")
                
                # Création et ajout des boutons "Oui" et "Non"
                bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
                bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
                
                msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

                msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
                # Vérifier quel bouton a été cliqué
                if msg_box.clickedButton() == bouton_oui:
                    reply_is_yes = True
                else:
                    reply_is_yes = False

                if not reply_is_yes:
                    return  # L'utilisateur a annulé
                if reply_is_yes:
                    DeleteSousCategorie(nom,categorie_parent)
                    self.load_tiers()
                    self.load_sous_categories()
                    self.load_operations()
                else:
                    return  # L'utilisateur a annulé
            else:
                # Il y a d'autres sous-catégories disponibles
                dialog = ReplaceSousCategoriePopup(autres_sous_categorie, self)
                if dialog.exec():
                    selected_value = dialog.get_selected_sous_categorie()
                    UpdateSousCategorieInOperations(nom, selected_value,categorie_parent)
                    UpdateSousCategorieTier(nom,selected_value,categorie_parent)
                    self.load_tiers()
                    self.load_sous_categories()
                    self.load_operations()
                    return
                else:
                    return  # L'utilisateur a annulé

        # Suppression de la sous-catégorie
        DeleteSousCategorie(nom,categorie_parent)
        self.load_sous_categories()
        self.load_tiers()
        self.load_operations()



    def delete_selected_categorie(self, row):
        item_nom = self.categorie_table.item(row, 0)
        nom = str(item_nom.data(Qt.ItemDataRole.UserRole))
        nb_operations_related = GetCategorieRelatedOperations(nom)
        sous_categorie = GetSousCategorie(nom)
        if len(sous_categorie) > 0:
            QMessageBox.warning(self,"Suppresion de catégorie impossible", "Impossible de supprimer la catégorie, des sous-catégories l'utilisent encore")
            return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation de suppression")
        msg_box.setText(f"Êtes-vous sûr de vouloir supprimer la catégorie '{nom}' ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_categorie = GetCategorieExceptCurrent(nom)

            if not autres_categorie:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Confirmation de suppression")
                msg_box.setText("Aucune autre catégorie disponible.\nVoulez-vous remplacer par une valeur vide ?")
                
                # Création et ajout des boutons "Oui" et "Non"
                bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
                bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
                
                msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

                msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
                # Vérifier quel bouton a été cliqué
                if msg_box.clickedButton() == bouton_oui:
                    reply_is_yes = True
                else:
                    reply_is_yes = False

                if not reply_is_yes:
                    return  # L'utilisateur a annulé

                # Aucun autre sous-catégorie dispo
                if reply_is_yes:
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
        tiers = GetTiersByType(nom)
        if len(tiers)> 0:
            QMessageBox.warning(self,"Suppresion du type de tiers impossible", "Impossible de supprimer le type de tiers, des tiers l'utilisent encore")
            return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation de suppression")
        msg_box.setText(f"Êtes-vous sûr de vouloir supprimer le type de tiers '{nom}' ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_type_tier = GetTypeTierExceptCurrent(nom)

            if not autres_type_tier:
                # Aucun autre sous-catégorie dispo
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Suppression type tiers")
                msg_box.setText("Aucun autre type de tiers disponible.\nVoulez-vous remplacer par une valeur vide ?")
                
                # Création et ajout des boutons "Oui" et "Non"
                bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
                bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
                
                msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

                msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
                # Vérifier quel bouton a été cliqué
                if msg_box.clickedButton() == bouton_oui:
                    reply_is_yes = True
                else:
                    reply_is_yes = False

                if not reply_is_yes:
                    return  # L'utilisateur a annulé
                if reply_is_yes:
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
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation de suppression")
        msg_box.setText(f"Êtes-vous sûr de vouloir supprimer le moyen de paiement '{nom}' ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé

        if nb_operations_related > 0:
            # Récupère la liste des autres sous-catégories possibles
            autres_moyen_paiement = GetMoyenPaiementExceptCurrent(nom)

            if not autres_moyen_paiement:
                # Aucun autre sous-catégorie dispo
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Suppression moyen de paiement")
                msg_box.setText("Aucun autre moyen de paiement disponible.\nVoulez-vous remplacer par une valeur vide ?")
                
                # Création et ajout des boutons "Oui" et "Non"
                bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
                bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
                
                msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

                msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
                # Vérifier quel bouton a été cliqué
                if msg_box.clickedButton() == bouton_oui:
                    reply_is_yes = True
                else:
                    reply_is_yes = False

                if not reply_is_yes:
                    return  # L'utilisateur a annulé
                if reply_is_yes:
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
            self.load_beneficiaire()

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


    def edit_selected_echeance(self, row):
        try:
            # Récupère l'ID de l'opération à partir d'une colonne cachée ou d'une donnée stockée
            echeance_id_item = self.echeance_table.item(row, 0)  # Assure-toi que l'ID est dans la colonne 0
            if not echeance_id_item:
                return

            echeance_id = echeance_id_item.data(Qt.ItemDataRole.UserRole)
            if not echeance_id:
                return

            # Récupérer l'objet Operation depuis la base de données
            echeance = GetEcheance(echeance_id)
            if not echeance:
                QMessageBox.warning(self, "Erreur", "Impossible de trouver l'echéance sélectionnée.")
                return
            if not echeance.is_position:
                # Ouvrir le dialogue en mode édition
                operation = Operation(echeance.prochaine_echeance,echeance.type,echeance.type_tier,echeance.tier,echeance.moyen_paiement,echeance.categorie,echeance.sous_categorie,echeance.debit,echeance.credit,echeance.notes,echeance.compte_id,"",echeance.compte_associe,"",type_beneficiaire=echeance.type_beneficiaire,beneficiaire = echeance.beneficiaire,_id = echeance_id)
                dialog = AddEditOperationDialog(
                parent=self,
                account_id=self.current_account,
                operation=operation,
                isEdit=True,
                isEcheance=True,
                echeance = echeance
            )
            else:
                position = Position(echeance.prochaine_echeance,echeance.type,echeance.tier,echeance.nb_part,echeance.val_part,echeance.frais,echeance.interets,echeance.notes,echeance.compte_id,round(echeance.nb_part*echeance.val_part,2),echeance.compte_associe,echeance._id)
                dialog = AddEditPositionDialog(
                parent=self,
                account_id=self.current_account,
                position=position,
                isEdit=True,
                isEcheance=True,
                echeance=echeance
            )
                
            dialog.exec()
            self.echeance_table.clearContents()
            self.load_echeance()           

        except Exception as e:
            print("Erreur lors de la modification de l'echeance:", e)
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")


    def forcer_selected_echeance(self,row):
        try:
            # Récupère l'ID de l'opération à partir d'une colonne cachée ou d'une donnée stockée
            echeance_id_item = self.echeance_table.item(row, 0)  # Assure-toi que l'ID est dans la colonne 0
            if not echeance_id_item:
                return

            echeance_id = echeance_id_item.data(Qt.ItemDataRole.UserRole)
            if not echeance_id:
                return

            # Récupérer l'objet Operation depuis la base de données
            echeance = GetEcheance(echeance_id)
            if not echeance:
                QMessageBox.warning(self, "Erreur", "Impossible de trouver l'echéance sélectionnée.")
                return

            RunEcheance(GetEcheanceForce(echeance_id))
            self.reset_filters()
            self.placement_table.clearContents()
            self.load_placement()
            self.compte_table.clearContents()
            self.load_comptes()
            self.account_list.clear()
            self.load_accounts()
            self.echeance_table.clearContents()
            self.load_echeance()
            QMessageBox.information(self,"Forçage réussi","L'opération a bien été écrite dans les comptes")

        except Exception as e:
            print("Erreur lors du forçage de l'échéance:", e)
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def edit_selected_historique_placement(self, row):
        # Récupérer les informations de la ligne sélectionnée
        date_int = int(datetime.datetime.strptime(self.history_table.item(row, 0).text(), "%d/%m/%Y").strftime("%Y%m%d"))
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
            self.position_table.clearContents()
            self.load_position()


    def delete_selected_historique_placement(self, row):
        # Récupérer les informations de la ligne sélectionnée
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Suppression de la valeur historique du placement")
        msg_box.setText("La valeur historique du placement va être supprimée\nEtes-vous sûr de vouloir supprimer cette valeur ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé
        
        if reply_is_yes:
            date_int = int(datetime.datetime.strptime(self.history_table.item(row, 0).text(), "%d/%m/%Y").strftime("%Y%m%d"))
            DeleteHistoriquePlacement(self.current_placement,date_int)
            self.show_placement_history_graph(self.placement_table.item(self.current_placement_row, 0))
            self.placement_table.clearContents()
            self.load_placement()
            self.account_list.clear()
            self.load_accounts()

    def delete_selected_echeance(self, row):
        # Récupérer les informations de la ligne sélectionnée
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Suppression de l'échéance")
        msg_box.setText("L'échéance va être supprimée\nEtes-vous sûr de vouloir supprimer cette valeur ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé
        
        if reply_is_yes:
            echeance_id_item = self.echeance_table.item(row, 0)  # Assure-toi que l'ID est dans la colonne 0
            if not echeance_id_item:
                return

            echeance_id = echeance_id_item.data(Qt.ItemDataRole.UserRole)
            if not echeance_id:
                return
            DeleteEcheance(echeance_id)
            self.load_echeance()



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

    def mark_r_selected_position(self,row):
        try:
            # Récupère l'ID de l'opération à partir d'une colonne cachée ou d'une donnée stockée
            position_id_item = self.position_table.item(row, 0)  # Assure-toi que l'ID est dans la colonne 0
            if not position_id_item:
                return

            position_id = position_id_item.data(Qt.ItemDataRole.UserRole)
            if not position_id:
                return
            
            MarkRPosition(str(position_id),1)
            self.position_table.clearContents()
            self.load_position()
            

        except Exception as e:
            print("Erreur lors de la modification de la position:", e)
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")


    def unmark_r_selected_position(self,row):
        try:
            # Récupère l'ID de l'opération à partir d'une colonne cachée ou d'une donnée stockée
            position_id_item = self.position_table.item(row, 0)  # Assure-toi que l'ID est dans la colonne 0
            if not position_id_item:
                return

            position_id = position_id_item.data(Qt.ItemDataRole.UserRole)
            if not position_id:
                return
            
            MarkRPosition(position_id,0)
            self.position_table.clearContents()
            self.load_position()
            

        except Exception as e:
            print("Erreur lors de la modification de la position:", e)
            QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite : {e}")

    def edit_selected_position(self, row, isEdit):
        try:
            # Récupère l'ID de l'opération à partir d'une colonne cachée ou d'une donnée stockée
            position_id_item = self.position_table.item(row, 0)  # Assure-toi que l'ID est dans la colonne 0
            if not position_id_item:
                return

            position_id = position_id_item.data(Qt.ItemDataRole.UserRole)
            if not position_id:
                return

            # Récupérer l'objet Operation depuis la base de données
            position = GetPosition(position_id)
            if not position:
                QMessageBox.warning(self, "Erreur", "Impossible de trouver la position sélectionnée.")
                return

            # Ouvrir le dialogue en mode édition
            dialog = AddEditPositionDialog(
            parent=self,
            account_id=self.current_account,
            position=position,
            isEdit=isEdit
        )
            if dialog.exec():
                self.load_position()

        except Exception as e:
            print("Erreur lors de la modification de la position:", e)
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

    def open_add_operation_dialog(self,isEcheance = False, echeance = None,compte_choisi_id = None):
        if self.current_account is not None or isEcheance:
            dialog = AddEditOperationDialog(self, self.current_account,isEcheance = isEcheance, echeance=echeance,compte_choisi_id = compte_choisi_id)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte d'abord.")

    def open_add_position_dialog(self,isEcheance = False, echeance = None, compte_choisi_id = None):
        if self.current_account is not None or isEcheance:
            dialog = AddEditPositionDialog(self, self.current_account,isEcheance = isEcheance, echeance=echeance, compte_choisi_id = compte_choisi_id)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte de placement d'abord.")

    def open_add_pret_dialog(self):
        if self.current_account is not None:
            dialog = AddEditLoanDialog(self,current_account=str(self.current_account))
            dialog.exec()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte de placement d'abord.")

    def open_edit_pret_dialog(self):
        if self.current_account is not None:
            l = GetLoan(self.current_account)
            dialog = AddEditLoanDialog(self,current_account=str(self.current_account),loan=l)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte de placement d'abord.")

    def add_tier_row(self, row, tier: Tier):
            item_nom = QTableWidgetItem(tier.nom)
            item_nom.setData(Qt.ItemDataRole.UserRole, tier._id)
            self.tier_table.setItem(row, 0, align(item_nom))

            self.tier_table.setItem(row, 1, align(QTableWidgetItem(tier.type)))
            self.tier_table.setItem(row, 2, align(QTableWidgetItem(tier.categorie)))
            self.tier_table.setItem(row, 3, align(QTableWidgetItem(tier.sous_categorie)))
            self.tier_table.setItem(row, 4, align(QTableWidgetItem(tier.moyen_paiement)))
            self.tier_table.setItem(row, 5, align(QTableWidgetItem("Actif" if tier.actif else "Inactif")))



    def add_sous_categorie_row(self, row, sous_cat: SousCategorie):
        item = QTableWidgetItem(sous_cat.nom)
        item.setData(Qt.ItemDataRole.UserRole, {
            "nom": sous_cat.nom,
            "categorie_parent": sous_cat.categorie_parent
        })
        self.sous_categorie_table.setItem(row, 0, align(item))
        self.sous_categorie_table.setItem(row, 1, align(QTableWidgetItem(sous_cat.categorie_parent)))

    def add_beneficiaire_row(self, row, beneficiaire: Beneficiaire):
        item = QTableWidgetItem(beneficiaire.nom)
        item.setData(Qt.ItemDataRole.UserRole,{
            "nom" : beneficiaire.nom,
            "type_beneficiaire": beneficiaire.type_beneficiaire})
        self.sous_categorie2_table.setItem(row, 0, align(item))
        self.sous_categorie2_table.setItem(row, 1, align(QTableWidgetItem(beneficiaire.type_beneficiaire)))

    def add_categorie_row(self, row,categorie : Categorie):
        item = QTableWidgetItem(categorie.nom)
        item.setData(Qt.ItemDataRole.UserRole,categorie.nom)
        self.categorie_table.setItem(row, 0, align(item))

    def add_type_beneficiaire_row(self, row,type_beneficiaire : TypeBeneficiaire):
        item = QTableWidgetItem(type_beneficiaire.nom)
        item.setData(Qt.ItemDataRole.UserRole,type_beneficiaire.nom)
        self.categorie2_table.setItem(row, 0, align(item))


    def add_moyen_paiement_row(self, row, mp: MoyenPaiement):
        item = QTableWidgetItem(mp.nom)
        item.setData(Qt.ItemDataRole.UserRole, mp.nom)
        self.moyen_paiement_table.setItem(row, 0, align(item))

    def add_type_tier_row(self, row, tt: TypeTier):
        item = QTableWidgetItem(tt.nom)
        item.setData(Qt.ItemDataRole.UserRole, tt.nom)
        self.type_tier_table.setItem(row, 0, align(item))

    def add_placement_row(self, row, placement: HistoriquePlacement):
        self.placement_table.setItem(row, 0, align(QTableWidgetItem(placement.nom)))
        self.placement_table.setItem(row, 1, align(QTableWidgetItem(placement.ticker)))
        self.placement_table.setItem(row, 2, align(QTableWidgetItem(placement.type)))
        self.placement_table.setItem(row, 3, align(DateTableWidgetItem(placement.date),Qt.AlignmentFlag.AlignCenter))
        self.placement_table.setItem(row, 4, align(NumericTableWidgetItem(placement.val_actualise, format_montant(placement.val_actualise,1)),Qt.AlignmentFlag.AlignRight))
        self.placement_table.setItem(row, 5, align(QTableWidgetItem(placement.origine)))
        

    def add_echeance_row(self, row, echeance: Echeance):
        frequence_item = DateTableWidgetItem(echeance.frequence)
        frequence_item.setData(Qt.ItemDataRole.UserRole, echeance._id)
        self.echeance_table.setItem(row, 0, align(frequence_item))
        self.echeance_table.setItem(row, 1, align(DateTableWidgetItem(echeance.echeance1),Qt.AlignmentFlag.AlignCenter))
        self.echeance_table.setItem(row, 2, align(DateTableWidgetItem(echeance.prochaine_echeance),Qt.AlignmentFlag.AlignCenter))
        self.echeance_table.setItem(row, 3, align(QTableWidgetItem(GetCompteName(echeance.compte_id))))
        self.echeance_table.setItem(row, 4, align(QTableWidgetItem(echeance.type)))
        self.echeance_table.setItem(row, 5, align(QTableWidgetItem(GetCompteName(echeance.compte_associe))))
        self.echeance_table.setItem(row, 6, align(QTableWidgetItem(echeance.type_tier)))
        self.echeance_table.setItem(row, 7, align(QTableWidgetItem(GetTierName(echeance.tier) if GetTierName(echeance.tier) is not None else echeance.tier)))
        self.echeance_table.setItem(row, 8, align(QTableWidgetItem(echeance.categorie)))
        self.echeance_table.setItem(row, 9, align(QTableWidgetItem(echeance.sous_categorie)))
        self.echeance_table.setItem(row, 10, align(QTableWidgetItem(echeance.moyen_paiement)))
        self.echeance_table.setItem(row, 11, align(QTableWidgetItem(echeance.type_beneficiaire)))
        self.echeance_table.setItem(row, 12, align(QTableWidgetItem(echeance.beneficiaire)))
        self.echeance_table.setItem(row, 13, align(NumericTableWidgetItem(echeance.debit, format_montant(echeance.debit)),Qt.AlignmentFlag.AlignRight))
        self.echeance_table.setItem(row, 14, align(NumericTableWidgetItem(echeance.credit, format_montant(echeance.credit)),Qt.AlignmentFlag.AlignRight))
        self.echeance_table.setItem(row, 15, align(NumericTableWidgetItem(echeance.nb_part, str(f"{float(echeance.nb_part):,.4f}".replace(",", " ").replace(".", ","))) if echeance.nb_part != 0 else QTableWidgetItem(""),Qt.AlignmentFlag.AlignRight))
        self.echeance_table.setItem(row, 16, align(NumericTableWidgetItem(echeance.val_part, format_montant(echeance.val_part,1) if echeance.type != "Intérêts" else "") ,Qt.AlignmentFlag.AlignRight))
        self.echeance_table.setItem(row, 17, align(NumericTableWidgetItem(echeance.frais, format_montant(echeance.frais)),Qt.AlignmentFlag.AlignRight))
        self.echeance_table.setItem(row, 18, align(NumericTableWidgetItem(echeance.interets, format_montant(echeance.interets)),Qt.AlignmentFlag.AlignRight))
        self.echeance_table.setItem(row, 19, align(QTableWidgetItem(echeance.notes)))

    def add_compte_row(self, row, compte: Compte):
        item_nom = QTableWidgetItem(str(compte.nom))
        item_nom.setData(Qt.ItemDataRole.UserRole, str(compte._id))
        self.compte_table.setItem(row, 0, item_nom)

        solde = compte.solde
        solde_str = f"{solde:,.2f}".replace(",", " ").replace(".", ",") + " €"
        if solde < 0:
            solde_str = solde_str.replace("-", "- ")
            color = QColor("#e74c3c")
        else:
            solde_str = "+ " + solde_str
            color = QColor("#2ecc71")

        item_solde = NumericTableWidgetItem(solde, solde_str)
        item_solde.setForeground(color)
        item_solde.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.compte_table.setItem(row, 1, item_solde)
        self.compte_table.setItem(row, 2, QTableWidgetItem(compte.type))
        self.compte_table.setItem(row, 3, QTableWidgetItem(compte.nom_banque))


    def load_operations(self, operations=None, solde=None):
        if self.current_account is None and (operations == [] or operations is None):
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
            debit_item.setForeground(QColor("#e74c3c"))
            debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_data[13] = debit_item
        elif operation.type.lower() in ["crédit", "transfert de"]:
            credit_formate = f"+ {operation.credit:,.2f}".replace(",", " ").replace(".", ",") + " €" if operation.credit > 0 else ""
            credit_item = NumericTableWidgetItem(operation.credit, credit_formate)
            credit_item.setForeground(QColor("#2ecc71"))
            credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row_data[14] = credit_item

        solde = previous_solde + operation.debit + operation.credit
        solde_formate = f"{solde:,.2f}".replace(",", " ").replace(".", ",")
        if solde < 0:
            solde_formate = solde_formate.replace("-","- ") + " €"
            solde_item = NumericTableWidgetItem(solde, solde_formate)
            solde_item.setForeground(QColor("#e74c3c"))
        else:
            solde_formate = "+ " + solde_formate + " €"
            solde_item = NumericTableWidgetItem(solde, solde_formate)
            solde_item.setForeground(QColor("#2ecc71"))
        solde_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row_data[16] = solde_item
        row_data['solde'] = solde
        return row_data

    def _add_row_to_table(self, row_index: int, row_data: dict):
        for col, item in row_data.items():
            if isinstance(item,NumericTableWidgetItem):
                self.transaction_table.setItem(row_index, col, align(item,Qt.AlignmentFlag.AlignRight))
            else :
                self.transaction_table.setItem(row_index, col, align(item))

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
                self.transaction_table.item(row, 10).setText("P")  # Colonne Bq
        self.account_list.clear()
        self.load_accounts()
        self.compte_table.clearContents()
        self.load_comptes()
        self.sound_effect("sound_effect/transaction.wav")

    def sound_effect(self,sound_path:str):
        sound_path = os.path.abspath(sound_path)
        if os.path.exists(sound_path):
            self.player.setSource(QUrl.fromLocalFile(sound_path))
            self.audio_output.setVolume(50)  # Volume entre 0 et 100
            self.player.play()
        else:
            print(f"Fichier son introuvable : {sound_path}")

    def add_pret_row(self, data: tuple):
        def format_number(value):
            """Formate un nombre en séparant les milliers par espaces, en conservant les décimales."""
            try:
                number = float(value)
                integer_part, dot, decimal_part = f"{number:.2f}".partition(".")
                formatted_integer = "{:,}".format(int(integer_part)).replace(",", " ")
                return f"{formatted_integer}{dot}{decimal_part}" if dot else formatted_integer
            except (ValueError, TypeError):
                return str(value)

        def make_item(value, background_color, alignment=Qt.AlignmentFlag.AlignRight,
                    item_type=QTableWidgetItem, format_numeric=True, suffix=""):
            if item_type is NumericTableWidgetItem:
                text_value = format_number(value) if format_numeric else str(value)
                item = item_type(value, f"{text_value}{suffix}")
            elif item_type is DateTableWidgetItem:
                item = item_type(value)
            else:
                item = item_type(f"{str(value)}{suffix}")

            item.setTextAlignment(alignment)
            item.setForeground(background_color)
            return item

        self.pret_table.setSortingEnabled(False)
        row = self.pret_table.rowCount()
        self.pret_table.insertRow(row)

        # Déterminer la couleur en fonction de la date
        echeance_date = int(data[1])
        today = int(date.today().strftime("%Y%m%d"))
        background_color = QColor("#2ecc71") if echeance_date <= today else QColor("#e74c3c")

        # Définition des colonnes : (valeur, type, [alignement], [format_numeric], [suffix])
        columns = [
            (data[0], NumericTableWidgetItem, Qt.AlignmentFlag.AlignLeft, False),
            (data[1], DateTableWidgetItem,Qt.AlignmentFlag.AlignCenter),
            (data[4], NumericTableWidgetItem, Qt.AlignmentFlag.AlignRight, True, " €"),  # €
            (data[5], NumericTableWidgetItem, Qt.AlignmentFlag.AlignRight, True, " €"),  # €
            (data[6], NumericTableWidgetItem, Qt.AlignmentFlag.AlignRight, True, " €"),  # €
            (data[7], NumericTableWidgetItem, Qt.AlignmentFlag.AlignRight, True, " €"),  # €
            (data[8], NumericTableWidgetItem, Qt.AlignmentFlag.AlignRight, True, " €"),  # €
            (int(str(data[1])[:4]), NumericTableWidgetItem, Qt.AlignmentFlag.AlignLeft, False),  # pas de formatage
            (data[3], NumericTableWidgetItem,Qt.AlignmentFlag.AlignRight, False, " %"),
            (data[2], NumericTableWidgetItem,Qt.AlignmentFlag.AlignRight, False, " %")
        ]

        for col_index, col_data in enumerate(columns):
            value, item_type, *rest = col_data
            alignment = rest[0] if rest and isinstance(rest[0], Qt.AlignmentFlag) else Qt.AlignmentFlag.AlignRight
            format_numeric = rest[1] if len(rest) >= 2 and isinstance(rest[1], bool) else True
            suffix = rest[2] if len(rest) >= 3 and isinstance(rest[2], str) else ""
            self.pret_table.setItem(row, col_index, make_item(value, background_color, alignment, item_type, format_numeric, suffix))

        self.pret_table.resizeColumnsToContents()
        self.pret_table.setSortingEnabled(True)


    def add_position_row(self, position: Position):
        compte_associe_name = ''
        if position.compte_associe != '':
            compte_associe_name = self.get_compte_name(position.compte_associe)

        self.position_table.setSortingEnabled(False)
        row = self.position_table.rowCount()
        date_item = DateTableWidgetItem(position.date)
        date_item.setData(Qt.ItemDataRole.UserRole, position._id)
        self.position_table.insertRow(row)
        self.position_table.setItem(row, 0, align(date_item,Qt.AlignmentFlag.AlignCenter))
        self.position_table.setItem(row, 1, align(QTableWidgetItem(position.type)))
        self.position_table.setItem(row, 2, align(QTableWidgetItem(compte_associe_name)))
        self.position_table.setItem(row, 3, align(QTableWidgetItem(position.nom_placement)))
        self.position_table.setItem(row, 4, align(QTableWidgetItem('R' if position.bq else ""),Qt.AlignmentFlag.AlignCenter))
        self.position_table.setItem(row, 5, align(NumericTableWidgetItem(position.nb_part, str(f"{float(position.nb_part):,.4f}".replace(",", " ").replace(".", ","))) if position.nb_part != 0 else QTableWidgetItem("") ,Qt.AlignmentFlag.AlignRight))
        self.position_table.setItem(row, 6, align(NumericTableWidgetItem(position.val_part, format_montant(position.val_part,1) if position.type != "Intérêts" else ""),Qt.AlignmentFlag.AlignRight))
        self.position_table.setItem(row, 7, align(NumericTableWidgetItem(position.frais, format_montant(position.frais)),Qt.AlignmentFlag.AlignRight))
        self.position_table.setItem(row, 8, align(NumericTableWidgetItem(position.interets, format_montant(position.interets)),Qt.AlignmentFlag.AlignRight))
        self.position_table.setItem(row, 9, align(QTableWidgetItem(position.notes)))
        self.position_table.setItem(row, 10, align(NumericTableWidgetItem(position.montant_investit, format_montant(position.montant_investit)),Qt.AlignmentFlag.AlignRight))
        self.position_table.setItem(row, 11, align(NumericTableWidgetItem(round(position.nb_part*position.val_part,2), format_montant(round(position.nb_part*position.val_part,2))),Qt.AlignmentFlag.AlignRight))
        self.position_table.resizeColumnsToContents()
        self.position_table.setSortingEnabled(True)


    def add_position(self, position:Position):
        InsertPosition(position)
        if position.type == TypePosition.Achat.value:
            InsertOperation(Operation(position.date,TypeOperation.TransfertV.value,"","","","","",round((position.nb_part*position.val_part * -1) - position.frais,2),0,f"Achat de {position.nb_part} parts de {position.nom_placement} à {position.val_part} €",position.compte_associe,compte_associe=position.compte_id,link = str(position._id)))
        elif position.type == TypePosition.Vente.value:
            InsertOperation(Operation(position.date,TypeOperation.TransfertD.value,"","","","","",0,round((position.nb_part*position.val_part * -1) - position.frais,2),f"Vente de {position.nb_part * -1} parts de {position.nom_placement} à {position.val_part} €",position.compte_associe,compte_associe=position.compte_id,link = str(position._id)))
        elif position.type == TypePosition.Interet.value:
            InsertOperation(Operation(position.date,TypeOperation.TransfertD.value,"","","","","",0,position.interets,f"Intérêts placement {position.nom_placement}",position.compte_associe,compte_associe=position.compte_id,link = str(position._id)))
        type_placement = GetTypePlacement(position.nom_placement)
        ticker = GetTickerPlacementByNomPlacement(position.nom_placement)
        last_value_placement = GetLastValueForPlacement(position.nom_placement)
        if not InsertHistoriquePlacement(HistoriquePlacement(position.nom_placement, type_placement, position.date, position.val_part, position.type,ticker)) and last_value_placement != position.val_part:
            # Ici on suppose que le conflit est dû à un doublon. Tu peux filtrer plus précisément avec l'erreur SQL si nécessaire.
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Conflit détecté")
            date_str = str(position.date)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            display_date = QDate(year, month, day).toString("dd/MM/yyyy")
            msg_box.setText(f"Une entrée pour ce placement existe déjà. (date : {display_date}, valeur connue : {last_value_placement} € )")
            msg_box.setInformativeText("Voulez-vous remplacer l'ancienne valeur par la nouvelle ?")
            msg_box.setIcon(QMessageBox.Icon.Warning)            
            # Création et ajout des boutons "Oui" et "Non"
            bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
            bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
            
            msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

            msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
            # Vérifier quel bouton a été cliqué
            if msg_box.clickedButton() == bouton_oui:
                reply_is_yes = True
            else:
                reply_is_yes = False

            if reply_is_yes:
                # Remplace l'ancienne valeur (mise à jour dans la BDD)
                DeleteHistoriquePlacement(position.nom_placement,position.date)
                InsertHistoriquePlacement(HistoriquePlacement(position.nom_placement, type_placement, position.date, position.val_part, position.type,ticker))
                QMessageBox.information(None, "Mise à jour", "L'historique des placements a été mise à jour avec succès.")
            else:
                # Ne rien faire, l'utilisateur a choisi de garder l'existant
                QMessageBox.information(None, "Annulé", "L'historique des placements n'a pas été mis à jour.")
        self.sound_effect("sound_effect/transaction.wav")
        self.account_list.clear()
        self.load_accounts()
        self.add_position_row(position)
        self.compte_table.clearContents()
        self.load_comptes()
        self.placement_table.clearContents()
        self.load_placement()

    def add_loan(self,pret:Loan):
        echeancier = calculer_echeancier_pret_avec_assurance(pret.montant_initial,pret.taux_annuel_initial,pret.duree_ans,pret.assurance_par_periode,pret.frequence_paiement,pret.date_debut,pret.taux_variables)
        compte_id = str(pret.compte_id)
        compte_associe = str(pret.compte_associe)
        InsertPret(compte_id,echeancier,compte_associe,pret.nom)
        new_solde,date = GetCRD(compte_id)
        if new_solde is None:
            new_solde = -1 * pret.montant_initial
        if date is None:
            date = int(echeancier[0]["date"].strftime('%Y%m%d'))
        
        echeance = Echeance(pret.frequence_paiement,int(echeancier[0]["date"].strftime('%Y%m%d')),date,"Débit","","","","",-1*echeancier[-1]["mensualite"],0,f"Remboursement prêt {pret.nom}",compte_associe,0,0,0,0,"Prélèvement",0,compte_associe=compte_id)
        # if echeance.echeance1 <= int(datetime.date.today().strftime("%Y%m%d")):
        #     operation = Operation(echeance.echeance1,"Débit","","","Prélèvement","","",echeance.debit,echeance.credit,echeance.notes,echeance.compte_id,"",echeance.compte_associe)
        #     InsertOperation(operation)
        InsertEcheance(echeance)
        UpdateSoldeCompte(self.current_account,new_solde)
        self.load_pret()
        self.account_list.clear()
        self.load_accounts()
        self.echeance_table.clearContents()
        self.load_echeance()
        self.compte_table.clearContents()
        self.load_comptes()


    def add_tier(self, tier: Tier):
        if InsertTier(tier,self):

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
        if InsertSousCategorie(sous_categorie,self):
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
        if InsertBeneficiaire(beneficiaire,self):
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
        if InsertCategorie(categorie,self):
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
        if InsertTypeBeneficiaire(type_beneficiaire,self):
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
        placement = Placement(historique_placement.nom,historique_placement.type, historique_placement.ticker)
        if InsertPlacement(placement,parent=self):
            if historique_placement.ticker == "":
                InsertHistoriquePlacement(historique_placement)
            else:
                try:
                    last_values = GetLastValuePlacement(placement.ticker,datetime.datetime.strptime(str(historique_placement.date), "%Y%m%d").strftime("%Y-%m-%d"))              
                    InsertHistoriquePlacement(HistoriquePlacement(placement.nom,placement.type,last_values[placement.ticker][0],last_values[placement.ticker][1],"Actualisation automatique",placement.ticker))
                except Exception as e:
                    DeletePlacement(placement.nom)
                    QMessageBox.critical(self,"Erreur",f"Pas de valeur trouvé pour le N° ISIN {historique_placement.ticker}, vérifiez l'état de votre connexion internet puis réessayez")

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
            self.placement_table.clearContents()
            self.load_placement()

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

    def update_sous_categorie(self, sous_categorie,old_nom,old_categorie):
        return UpdateSousCategorie(sous_categorie,old_nom,old_categorie,self)

    def update_beneficiaire(self, beneficiaire,old_nom,old_type_beneficiaire):
        return UpdateBeneficiaire(beneficiaire,old_nom,old_type_beneficiaire,self)

    def update_categorie(self, categorie,old_nom):
        UpdateCategorie(categorie,old_nom)

    def update_type_beneficiaire(self, type_beneficiare,old_nom):
        UpdateTypeBeneficiaire(type_beneficiare,old_nom)

    def update_type_tier(self, type_tier,old_nom):
        UpdateTypeTypeTier(type_tier,old_nom)

    def update_placement(self, placement:HistoriquePlacement,old_nom):
        UpdatePlacement(placement,old_nom)
        UpdateHistoriquePlacement(placement,old_nom)        
        if placement.ticker != '':
            try:
                last_values = GetLastValuePlacement(placement.ticker)                
                InsertHistoriquePlacement(HistoriquePlacement(placement.nom,placement.type,last_values[placement.ticker][0],last_values[placement.ticker][1],"Actualisation automatique",placement.ticker))
                self.account_list.clear()
                self.load_accounts()
                self.placement_table.clearContents()
                self.load_placement()
            except:
                self.placement_table.clearContents()
                self.load_placement()
            



    def update_moyen_paiement(self, moyen_paiement,old_nom):
        UpdateMoyenPaiement(moyen_paiement,old_nom)

    def update_account(self, compte):
        UpdateCompte(compte)
        self.account_list.clear()
        self.load_accounts()

    def update_loan(self,loan:Loan):
        DeletePret(self.current_account)
        DeleteEcheancePret(loan.compte_id)
        self.add_loan(loan)

    def update_operation(self, operation:Operation,old_credit,old_debit,isEdit):
        if isEdit:
            DeleteOperation(operation,old_credit,old_debit)
            InsertOperation(operation)
        else:
            operation._id = str(ObjectId())
            operation.bq = 0
            InsertOperation(operation)
            self.sound_effect("sound_effect/transaction.wav")
        self.account_list.clear()
        self.load_accounts()
        self.load_operations()

    def update_position(self, position:Position,isEdit):
        if isEdit:
            DeletePosition(position)
            o = GetLinkOperation(str(position._id))
            DeleteOperation(o,o.credit,o.debit)
            self.add_position(position)         
        else:
            position._id = str(ObjectId())
            InsertPosition(position)
        self.account_list.clear()
        self.load_accounts()
        self.position_table.clearContents()
        self.load_position()

    def show_about(self):
        QMessageBox.information(self, "À propos", "Money v1.0\nPropriété de Langello Corp et de tous ses ayants droits.")

    def open_db(self):
        """
        Ouvre un explorateur de fichiers pour sélectionner des fichiers .db.
        """
        file_filter = "Fichiers de base de données (*.db);;Tous les fichiers (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier .db",
            "",
            file_filter
        )

        if file_path:
            self.current_db_path = file_path
            self.set_current_db(self.current_db_path)
        else:
            QMessageBox.warning(
                self,
                "Aucun fichier",
                "Aucun fichier de base de données sélectionné."
            )
            self.current_db_path = None # Réinitialiser si aucun fichier n'est sélectionné

    def open_qif(self):
        """
        Ouvre un explorateur de fichiers pour sélectionner des fichiers .qif.
        """
        file_filter = "Fichiers de base de données (*.qif);;Tous les fichiers (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier .qif",
            "",
            file_filter
        )

        if not file_path:
            QMessageBox.warning(
                self,
                "Aucun fichier",
                "Aucun fichier qif sélectionné."
            )
        return file_path
    
    def import_qif(self):
        input_path = self.open_qif()
        comptes = GetComptesHorsPlacement()
        import_dialog = ImportDialog(comptes, self)
        import_dialog.exec()
        compte_id = import_dialog.get_selected_compte_id()

        if compte_id:
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

            try:
                import_qif_data(input_path, compte_id, self.current_db_path)
            finally:
                QApplication.setOverrideCursor(QCursor(Qt.CursorShape.ArrowCursor))
                QMessageBox.information(self, "Importation terminée", f"Importation du fichier {input_path.split('/')[-1]} terminée")
                self.account_list.clear()
                self.load_accounts()
                self.categorie_table.clearContents()
                self.load_categorie()
                self.sous_categorie_table.clearContents()
                self.load_sous_categories()
                self.categorie2_table.clearContents()
                self.load_beneficiaire()
                self.sous_categorie2_table.clearContents()
                self.load_type_beneficiaire()
                self.tier_table.clearContents()
                self.load_tiers()
                self.transaction_table.clearContents()
                self.load_operations()


        

    def new_db(self):
        """
        Permet à l'utilisateur de créer une nouvelle base de données SQLite (.db).
        """
        # Propose un répertoire par défaut, par exemple le répertoire des documents de l'utilisateur
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        
        # Propose un nom de fichier par défaut
        default_filename = os.path.join(default_dir, "ma_nouvelle_base.db") # Nom de fichier par défaut plus explicite

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Créer une nouvelle base de données",
            default_filename,
            "Fichiers de base de données SQLite (*.db);;Tous les fichiers (*.*)"
        )

        if file_path:
            # S'assurer que l'extension .db est présente
            if not file_path.lower().endswith(".db"):
                file_path += ".db"
            
            # Tenter de définir et d'initialiser la nouvelle DB
            self.set_current_db(file_path, is_new=True) # Important: c'est une nouvelle DB
        else:
            QMessageBox.information(
                self,
                "Opération annulée",
                "Création de la nouvelle base de données annulée."
            )

    def set_current_db(self, db_path, is_new=False):
        """Définit le chemin de la DB actuelle et initialise/sauvegarde."""
        self.current_db_path = db_path
        self.save_last_db_path(db_path)

        try:
            # create_tables va créer les tables si elles n'existent pas
            create_tables(self.current_db_path)
            if is_new:
                QMessageBox.information(
                    self,
                    "Nouvelle base de données",
                    f"La nouvelle base de données '{os.path.basename(self.current_db_path)}' a été créée avec succès."
                )
            else:
                 QMessageBox.information(
                    self,
                    "Fichier sélectionné",
                    f"Le fichier de base de données '{os.path.basename(self.current_db_path)}' a été chargé avec succès."
                )
            self.run_echeance_if_db_ready()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de base de données",
                f"Erreur lors de l'initialisation des tables pour '{os.path.basename(self.current_db_path)}' : {e}\n"
                "Le fichier pourrait être corrompu ou les permissions insuffisantes."
            )
            self.current_db_path = None
            self.settings.remove("last_db_path")
        
        self.update_ui_for_db_status()
        # Tenter de charger la dernière DB utilisée
        self.load_last_db_path()

        # Configurer l'interface utilisateur
        self.setup_ui()

        # Gérer la logique de démarrage de la DB
        self.initialize_db_on_startup()

        # Maximiser la fenêtre
        self.showMaximized()

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

        panel.addWidget(self.account_list)
        panel.addWidget(add_account_btn)

        panel_widget = QWidget()
        panel_widget.setLayout(panel)
        panel_widget.setMaximumWidth(700)

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
            "Débit", "Crédit", "Notes", "Solde"
        ])
        table_style(self.transaction_table)
        self.transaction_table.resizeColumnsToContents()
        self.transaction_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.transaction_table.setSortingEnabled(True)
        self.transaction_table.setAlternatingRowColors(True)
        self.transaction_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.transaction_table.customContextMenuRequested.connect(self.show_context_menu_operation)
        self.transaction_table.cellClicked.connect(self.handle_table_click)

        self.position_table = QTableWidget(0, 12)
        self.position_table.setHorizontalHeaderLabels([
            "Date", "Type", "Compte\nAssocié", "Placement","Bq", "Nombre\nparts", "Valeur\npart Achat", "Frais", "Intérêts", "Notes", "Montant\nInvestissement", "Montant\nPosition initial"
        ])
        table_style(self.position_table)
        self.position_table.resizeColumnsToContents()
        self.position_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.position_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.position_table.sortItems(0,Qt.SortOrder.AscendingOrder)
        self.position_table.customContextMenuRequested.connect(self.show_context_menu_position)
        self.position_table.setSortingEnabled(True)
        self.position_table.setAlternatingRowColors(True)

        self.pret_table = QTableWidget(0,10)
        self.pret_table.setHorizontalHeaderLabels([
            "N°\nEch", "Date", "Capital restant\n dû", "Intérêts", "Capital", "Assurance", "Total", "Années", "Taux\nPériode", "Taux"
        ])
        table_style(self.pret_table)
        self.pret_table.resizeColumnsToContents()
        self.pret_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.pret_table.setSortingEnabled(True)
        self.pret_table.setAlternatingRowColors(True)

        # Stack pour alterner entre transactions et placements
        self.table_stack = QStackedLayout()
        self.table_stack.addWidget(self.transaction_table)
        self.table_stack.addWidget(self.position_table)
        self.table_stack.addWidget(self.pret_table) 

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
        self.pointage_info_label.setStyleSheet("font-weight: bold; color: #ffffff;")
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
        self.type_tiers_label = QLabel()
        self.filter_group_box = QGroupBox("Filtres")
        filter_vbox = QVBoxLayout()
        self.filter_group_box.setLayout(filter_vbox)
        filter_vbox.setContentsMargins(10, 10, 10, 10)
        filter_vbox.setSpacing(5)

        filter_hbox1 = QHBoxLayout()



        self.bq_filter = QCheckBox()
        self.bq_filter.setTristate(True)
        self.bq_filter.setCheckState(Qt.CheckState.PartiallyChecked)

        self.date_debut_filter = CustomDateEdit()
        self.date_debut_filter.setDate(QDate.currentDate().addMonths(-1))  # Par défaut, 1 mois avant

        self.date_fin_filter = CustomDateEdit()
        self.date_fin_filter.setDate(QDate.currentDate())  # Aujourd'hui

        self.tiers_filter = CheckableComboBox()
        self.tiers_filter.setPlaceholderText("Selectionner...")


        self.type_tiers_filter = CheckableComboBox()
        self.type_tiers_filter.setPlaceholderText("Selectionner...")


        # Récupère les noms des tiers
        tiers_noms = [tier.nom for tier in GetTiers()]
        self.tiers_nom_to_id = {}

        # Ajout dans le combo
        for tier in GetTiers():
            self.tiers_filter.addItem(tier.nom)
            self.tiers_nom_to_id[tier.nom] = str(tier._id)
        self.tiers_filter.setEditable(True)
        tiers_completer = QCompleter(tiers_noms, self)
        tiers_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        tiers_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        # Attache le completer au champ
        self.tiers_filter.setCompleter(tiers_completer)

        for type_tiers in GetTypeTier():
            self.type_tiers_filter.addItem(type_tiers.nom)
        # Tu peux alimenter ces ComboBox avec tes vraies données plus tard
        self.categorie_filter = CheckableComboBox()
        self.categorie_filter.setPlaceholderText("Selectionner...")

        self.sous_categorie_filter = CheckableComboBox()
        self.sous_categorie_filter.setPlaceholderText("Selectionner...")

        # Remplir les catégories
        for cat in GetCategorie():
            self.categorie_filter.addItem(cat.nom)
        for sous_cat in GetSousCategorieFiltre():
            self.sous_categorie_filter.addItem(sous_cat.nom)

        self.compte_filter = CheckableComboBox()
        self.compte_filter.setPlaceholderText("Selectionner...")

        self.comptes_nom_to_id = {}
        for compte in GetComptes():
            if compte.type in ["Courant","Epargne"]:
                self.compte_filter.addItem(compte.nom)
                self.comptes_nom_to_id[compte.nom] = str(compte._id)

        self.apply_filter_btn = QPushButton("Appliquer les filtres")
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        self.reset_filter_button = QPushButton("Réinitialiser les filtres")
        self.reset_filter_button.clicked.connect(self.reset_filters)

        filter_hbox1.addWidget(QLabel("Date début période:"))
        filter_hbox1.addWidget(self.date_debut_filter)
        filter_hbox1.addWidget(QLabel("Date fin période:"))
        filter_hbox1.addWidget(self.date_fin_filter)
        filter_hbox1.addWidget(QLabel("Pointées:"))
        filter_hbox1.addWidget(self.bq_filter)
        filter_hbox1.addStretch(1)
        filter_vbox.addLayout(filter_hbox1)

        # --- Filtres principaux (dates, pointées) ---
        right_panel.addLayout(filter_vbox)  # Tu peux garder le layout grille pour les filtres date & pointées

        # --- Filtres avancés (tiers, catégorie, sous-catégorie + boutons) ---

        # Colonne Tiers
        tiers_col = QHBoxLayout()
        tiers_col.addWidget(QLabel("Tiers:"))
        tiers_col.addWidget(self.tiers_filter)

        # Colonne Tiers
        type_tiers_col = QHBoxLayout()
        type_tiers_col.addWidget(QLabel("Type de tiers:"))
        type_tiers_col.addWidget(self.type_tiers_filter)

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
        filter_hbox2 = QHBoxLayout()
        filter_hbox2.addLayout(tiers_col)
        filter_hbox2.addLayout(type_tiers_col)
        filter_hbox2.addLayout(comptes_col)
        filter_hbox2.addLayout(cat_col)
        filter_hbox2.addLayout(sous_cat_col)
        filter_hbox2.addStretch(1)
        filter_vbox.addLayout(filter_hbox2)

        # --- Ligne boutons Appliquer / Réinitialiser ---
        apply_reset_layout = QHBoxLayout()
        self.apply_filter_btn_operation = QPushButton("Appliquer les filtres")
        self.apply_filter_btn_operation.clicked.connect(self.apply_filters)

        self.reset_filter_button_operation = QPushButton("Réinitialiser les filtres")
        self.reset_filter_button_operation.clicked.connect(self.reset_filters)
        self.current_account_label = QLabel()
        self.current_account_label.setVisible(False)
        right_panel.addWidget(self.current_account_label)
        right_panel.addWidget(self.filter_group_box)
        apply_reset_layout.addWidget(self.apply_filter_btn_operation)
        apply_reset_layout.addWidget(self.reset_filter_button_operation)

        # Ajout à l'interface
        right_panel.addLayout(apply_reset_layout)


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
        self.tier_table.setHorizontalHeaderLabels(["Nom", "Type", "Catégorie\ndéfaut", "Sous-\ncatégorie\ndéfaut", "Moy de\npaiement\ndéfaut", "Actif"])
        self.tier_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_style(self.tier_table)
        self.tier_table.resizeColumnsToContents()
        self.tier_table.setAlternatingRowColors(True)
        self.tier_table.setSortingEnabled(True)
        self.tier_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tier_table.sortItems(0,Qt.SortOrder.AscendingOrder)
        self.tier_table.customContextMenuRequested.connect(self.show_context_menu_tier)
        tiers_section.addWidget(self.tier_table)
        add_btn = QPushButton("Ajouter un tiers")
        add_btn.clicked.connect(self.open_add_tier_dialog)
        tiers_section.addWidget(add_btn)

        types_section = QVBoxLayout()
        self.type_tier_table = QTableWidget(0, 1)
        self.type_tier_table.setHorizontalHeaderLabels(["Type\nde\nTiers"])
        self.type_tier_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_style(self.type_tier_table)
        self.type_tier_table.resizeColumnsToContents()
        self.type_tier_table.setAlternatingRowColors(True)
        self.type_tier_table.setSortingEnabled(True)
        self.type_tier_table.sortItems(1,Qt.SortOrder.AscendingOrder)
        self.type_tier_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.type_tier_table.customContextMenuRequested.connect(self.show_context_menu_type_tier)
        types_section.addWidget(self.type_tier_table)
        add_type_btn = QPushButton("Ajouter type de tiers")
        add_type_btn.clicked.connect(self.open_add_type_tier_dialog)
        types_section.addWidget(add_type_btn)
        self.type_tier_table.itemClicked.connect(self.on_type_tier_clicked)

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
        table_style(self.categorie_table)
        self.categorie_table.resizeColumnsToContents()
        self.categorie_table.setAlternatingRowColors(True)
        self.categorie_table.sortItems(1,Qt.SortOrder.AscendingOrder)
        self.categorie_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.categorie_table.customContextMenuRequested.connect(self.show_context_menu_categorie)
        cat_section.addWidget(self.categorie_table)
        add_btn = QPushButton("Ajouter une catégorie")
        add_btn.clicked.connect(self.open_add_categorie_dialog)
        cat_section.addWidget(add_btn)
        self.categorie_table.itemClicked.connect(self.on_categorie_clicked)

        sous_cat_section = QVBoxLayout()
        self.sous_categorie_table = QTableWidget(0, 2)
        self.sous_categorie_table.setHorizontalHeaderLabels(["Sous-Catégorie", "Catégorie"])
        self.sous_categorie_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_style(self.sous_categorie_table)
        self.sous_categorie_table.resizeColumnsToContents()
        self.sous_categorie_table.setAlternatingRowColors(True)
        self.sous_categorie_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sous_categorie_table.customContextMenuRequested.connect(self.show_context_menu_sous_categorie)
        sous_cat_section.addWidget(self.sous_categorie_table)
        add_btn2 = QPushButton("Ajouter une sous-catégorie")
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
        table_style(self.compte_table)
        self.compte_table.resizeColumnsToContents()
        self.compte_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.compte_table.setAlternatingRowColors(True)
        self.compte_table.setSortingEnabled(True)
        self.compte_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.compte_table.sortItems(0,Qt.SortOrder.AscendingOrder)
        self.compte_table.customContextMenuRequested.connect(self.show_context_menu_compte)
        layout.addWidget(self.compte_table)
        add_btn = QPushButton("Ajouter un compte")
        add_btn.clicked.connect(self.open_add_account_dialog)
        layout.addWidget(add_btn)
        self.load_comptes()

    def setup_moyen_paiement_tab(self):
        layout = QVBoxLayout(self.moyen_paiement_tab)
        self.moyen_paiement_table = QTableWidget(0, 1)
        self.moyen_paiement_table.setHorizontalHeaderLabels(["Nom"])
        table_style(self.moyen_paiement_table)
        self.moyen_paiement_table.resizeColumnsToContents()
        self.moyen_paiement_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.moyen_paiement_table.setAlternatingRowColors(True)
        self.moyen_paiement_table.setSortingEnabled(True)
        self.moyen_paiement_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.moyen_paiement_table.sortItems(0,Qt.SortOrder.AscendingOrder)
        self.moyen_paiement_table.customContextMenuRequested.connect(self.show_context_menu_moyen_paiement)
        layout.addWidget(self.moyen_paiement_table)
        add_btn = QPushButton("Ajouter un moyen de paiement")
        add_btn.clicked.connect(self.open_add_moyen_paiement_dialog)
        layout.addWidget(add_btn)
        self.load_moyen_paiement()

    def setup_categories2_tab(self):
        layout = QHBoxLayout(self.categories2_tab)

        cat2_section = QVBoxLayout()
        self.categorie2_table = QTableWidget(0, 1)
        self.categorie2_table.setHorizontalHeaderLabels(["Type Bénéficiaire"])
        table_style(self.categorie2_table)
        self.categorie2_table.resizeColumnsToContents()
        self.categorie2_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.categorie2_table.setAlternatingRowColors(True)
        self.categorie2_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.categorie2_table.customContextMenuRequested.connect(self.show_context_menu_type_beneficiaire)
        cat2_section.addWidget(self.categorie2_table)
        btn_cat2 = QPushButton("Ajouter un type de bénéficiaire")
        btn_cat2.clicked.connect(self.open_add_type_beneficiaire_dialog)
        cat2_section.addWidget(btn_cat2)
        self.categorie2_table.itemClicked.connect(self.on_categorie2_clicked)

        sous_cat2_section = QVBoxLayout()
        self.sous_categorie2_table = QTableWidget(0, 2)
        self.sous_categorie2_table.setHorizontalHeaderLabels(["Bénéficiaire", "Type bénéficiaire"])
        table_style(self.sous_categorie2_table)
        self.sous_categorie2_table.resizeColumnsToContents()
        self.sous_categorie2_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sous_categorie2_table.setAlternatingRowColors(True)
        self.sous_categorie2_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sous_categorie2_table.customContextMenuRequested.connect(self.show_context_menu_sous_categorie2)
        sous_cat2_section.addWidget(self.sous_categorie2_table)
        btn_sous_cat2 = QPushButton("Ajouter un bénéficiaire")
        btn_sous_cat2.clicked.connect(self.open_add_beneficiaire_dialog)
        sous_cat2_section.addWidget(btn_sous_cat2)

        layout.addLayout(cat2_section)
        layout.addLayout(sous_cat2_section)

        self.load_type_beneficiaire()
        self.load_beneficiaire()

    def show_placement_history_graph(self, item):
        import locale
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        row = item.row()
        nom = self.placement_table.item(row, 0).text()
        self.current_placement = nom
        self.current_placement_row = row

        historique = GetHistoriquePlacement(nom)
        if not historique:
            self.graph_view.setHtml("<p>Aucune donnée historique disponible.</p>")
            return

        from datetime import datetime
        dates = [datetime.strptime(str(h.date).zfill(8), "%Y%m%d") for h in historique]
        valeurs = [h.val_actualise for h in historique]
        fig = go.Figure(data=[go.Scatter(x=dates, y=valeurs, mode='lines', name=nom)])
        dates = [f"{str(h.date)[6:8]}/{str(h.date)[4:6]}/{str(h.date)[0:4]}" for h in historique]

        self.history_table.setRowCount(0)  # Réinitialiser
        for date, valeur in zip(dates,valeurs):
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)
            self.history_table.setItem(row_position, 0, QTableWidgetItem(date))
            valeur_formate = f"{valeur:,.4f}".replace(",", " ").replace(".", ",").replace("-", "- ") + " €"
            valeur_item = NumericTableWidgetItem(valeur, valeur_formate)
            valeur_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.history_table.setItem(row_position, 1, valeur_item)

        self.history_table.resizeColumnsToContents()

        self.history_table.setVisible(True)
        

        bg_color = "#1e1e1e"
        font_color = "#ffffff"

        fig.update_layout(
            title=f"Évolution de {nom}",
            xaxis_title='Date',
            yaxis_title='Valeur',
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font=dict(color=font_color),
            xaxis=dict(
                type="date",
                tickformat="%d %b %Y",
                tickangle=-45,         
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                zeroline=False
            )
        )

        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>body {{ margin: 0; background-color: {bg_color}; }}</style>
        </head>
        <body>
            <div id="graph" style="width:100%; height:100%; max-height:450px;"></div>
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
        self.placement_table = QTableWidget(0, 6)        
        self.placement_table.setHorizontalHeaderLabels(["Nom", "N° ISIN", "Type", "Date", "Valeur actualisée", "Origine"])
        table_style(self.placement_table)
        self.placement_table.resizeColumnsToContents()
        self.placement_table.setAlternatingRowColors(True)
        self.placement_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.placement_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.placement_table.sortItems(0,Qt.SortOrder.AscendingOrder)
        self.placement_table.customContextMenuRequested.connect(self.show_context_menu_placement)
        self.placement_table.itemClicked.connect(self.show_placement_history_graph)

        add_placement_btn = QPushButton("Ajouter Placement")
        add_placement_btn.clicked.connect(self.open_add_placement_dialog)

        placement_table_panel.addWidget(self.placement_table)
        placement_table_panel.addWidget(add_placement_btn)

        # -- Panneau historique avec un layout vertical contenant le label + tableau --
        history_panel = QVBoxLayout()

        self.history_table = QTableWidget(0, 2)
        self.history_table.setHorizontalHeaderLabels(["Date", "Valeur"])
        table_style(self.history_table)
        self.history_table.resizeColumnsToContents()
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setMinimumWidth(250)
        self.history_table.setVisible(False)  # Caché initialement
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu_historique_placement)

        history_panel.addWidget(self.history_table)

        # Ajout au layout horizontal principal
        placement_main_panel.addLayout(placement_table_panel, stretch=3)
        placement_main_panel.addLayout(history_panel, stretch=1)

        # Ajout au layout principal vertical
        placement_layout.addLayout(placement_main_panel)

        # === 2. Web view pour le graphique en bas ===
        bg_color = "#1e1e1e"
        font_color = "#ffffff"
        self.graph_view = QWebEngineView()
        self.graph_view.setMinimumHeight(250)
        self.graph_view.setHtml(f"""<head>
            <meta charset="UTF-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>body {{ margin: 0; background-color: {bg_color}; color: {font_color} }}</style>
        </head><h3>Sélectionnez un placement pour voir l'historique.</h3>""")
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
            solde_label.setStyleSheet("font-weight: bold; color: #2ecc71;")
        else:
            solde_label.setStyleSheet("font-weight: bold; color: #e74c3c;")

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
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirmation")
        msg_box.setText("Supprimer ce tier ?")
        
        # Création et ajout des boutons "Oui" et "Non"
        bouton_oui = msg_box.addButton("Oui", QMessageBox.ButtonRole.YesRole)
        bouton_non = msg_box.addButton("Non", QMessageBox.ButtonRole.NoRole)
        
        msg_box.setIcon(QMessageBox.Icon.Question) # Ajoute une icône de question

        msg_box.exec() # Affiche la boîte de dialogue et attend la réponse
        # Vérifier quel bouton a été cliqué
        if msg_box.clickedButton() == bouton_oui:
            reply_is_yes = True
        else:
            reply_is_yes = False

        if not reply_is_yes:
            return  # L'utilisateur a annulé
        if reply_is_yes:
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
        voir_compte_action = QAction("Voir comptes associés",self)

        edit_action.triggered.connect(lambda: self.edit_selected_placement(row))
        delete_action.triggered.connect(lambda: self.delete_selected_placement(row))
        actualiser_action.triggered.connect(lambda: self.actualiser_selected_placement(row))
        voir_compte_action.triggered.connect(lambda:self.voir_compte_selected_placement(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(actualiser_action)
        menu.addAction(voir_compte_action)

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

    def show_context_menu_position(self, pos: QPoint):
        item = self.position_table.itemAt(pos)
        if not item or self.pointage_state["actif"] :
            return

        row = item.row()

        bq = self.position_table.item(row, 4).data(2)

        menu = QMenu(self)

        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)
        markr_action = QAction("Marquer comme rapproché", self)
        unmarkr_action = QAction("Marquer comme non rapproché", self)

        edit_action.triggered.connect(lambda: self.edit_selected_position(row,True))
        delete_action.triggered.connect(lambda: self.delete_selected_position(row))
        markr_action.triggered.connect(lambda: self.mark_r_selected_position(row))
        unmarkr_action.triggered.connect(lambda: self.unmark_r_selected_position(row))


        menu.addAction(edit_action)
        menu.addAction(delete_action)
        if bq != '':
            menu.addAction(unmarkr_action)
        else:
            menu.addAction(markr_action)

        menu.exec(self.position_table.viewport().mapToGlobal(pos))

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


    def show_context_menu_echeancier(self, pos: QPoint):
        item = self.echeance_table.itemAt(pos)
        if not item:
            return

        row = item.row()

        menu = QMenu(self)

        edit_action = QAction("Modifier", self)
        delete_action = QAction("Supprimer", self)
        forcer_action = QAction("Forcer l'écriture dans les comptes", self)

        edit_action.triggered.connect(lambda: self.edit_selected_echeance(row))
        delete_action.triggered.connect(lambda: self.delete_selected_echeance(row))
        forcer_action.triggered.connect(lambda: self.forcer_selected_echeance(row))

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(forcer_action)

        menu.exec(self.echeance_table.viewport().mapToGlobal(pos))

    def apply_filters(self):
        if self.current_account is None:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte d'abord.")
            return
        self.pointage_btn.setEnabled(False)
        selected_categories = set(self.categorie_filter.checkedItems())
        selected_type_tiers = set(self.type_tiers_filter.checkedItems())
        selected_sous_categories = set(self.sous_categorie_filter.checkedItems())
        selected_tiers = [
            self.tiers_nom_to_id[nom]
            for nom in self.tiers_filter.checkedItems()
            if nom in self.tiers_nom_to_id
        ]

        selected_comptes = []
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

        try:
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
            self.load_operations(GetFilteredOperations(date_debut,date_fin,selected_categories,selected_sous_categories,selected_tiers,selected_comptes,bq,selected_type_tiers),0)
        finally:
            # Always restore the cursor to the default after the operation
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.ArrowCursor)) # Example for PyQt/PySide
            self.transaction_table.setColumnHidden(16,True)

        
        

    def reset_filters(self):
        # Vider les sélections
        self.categorie_filter.clear()
        self.sous_categorie_filter.clear()
        self.tiers_filter.clear()
        self.type_tiers_filter.clear()
        self.compte_filter.clear()
        self.pointage_btn.setEnabled(True)
        self.categorie_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.categorie_filter.addSpecialItem("Tout désélectionner", "deselect_all")
        for cat in GetCategorie():
            self.categorie_filter.addItem(cat.nom)
        self.sous_categorie_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.sous_categorie_filter.addSpecialItem("Tout désélectionner", "deselect_all")
        for sous_cat in GetSousCategorieFiltre():
            self.sous_categorie_filter.addItem(sous_cat.nom)
        self.tiers_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.tiers_filter.addSpecialItem("Tout désélectionner", "deselect_all")
        for tier in GetTiers():
            self.tiers_filter.addItem(tier.nom)
        self.type_tiers_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.type_tiers_filter.addSpecialItem("Tout désélectionner", "deselect_all")
        for type_tier in GetTypeTier():
            self.type_tiers_filter.addItem(type_tier.nom)
        self.compte_filter.addSpecialItem("Tout sélectionner", "select_all")
        self.compte_filter.addSpecialItem("Tout désélectionner", "deselect_all")
        for compte in GetComptes():
            if compte.type in ["Courant","Epargne"]:
                self.compte_filter.addItem(compte.nom)
        if self.current_account is not None:
            self.compte_filter.checkItemByText(GetCompteName(self.current_account))
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

        solde, date = GetDerniereValeurPointe(self.current_account)
        result = show_pointage_dialog(self, solde, str(date))

        if result:
            self.pointage_state['actif'] = True
            self.pointage_state['somme_pointees'] = 0
            self.pointage_state['solde'] = result['solde']
            self.pointage_state['date'] = result['date']
            self.pointage_state['solde'] = solde
            self.pointage_state['target'] = result['solde']

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
            self.transaction_table.item(row, 10).setText("P")  # Colonne Bq

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
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    qss = """
    QPushButton {
        background-color: #000000; 
        color: #e0e0e0; 
        border: 2px solid #007ACC;
        border-radius: 5px;
        padding: 8px 15px;
        font-size: 18px;
        min-width: 120px;
        margin: 5px;
    }

    QTabBar::tab:selected{
    background: #0078d7;
    color:white;
    font-weight:bold;
}

    QPushButton:hover {
        background-color: #5A5A5A;
        color: #ffffff;
        border: 2px solid #0096FF;
    }

    QPushButton:pressed {
        background-color: #2F2F2F;
        color: #cccccc;
        border: 2px solid #005699;
    }

    QPushButton:disabled {
        background-color: #303030;
        color: #808080;
        border: 1px solid #404040;
    }
    *{ font-size : 18px
                      }
    """
    app.setStyleSheet(qss)
    window = MoneyManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
