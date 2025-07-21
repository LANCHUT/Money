from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QSettings, QStandardPaths, QUrl # Importez QUrl pour QMediaPlayer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput # Importez depuis QtMultimedia
import sys
import os
import GestionBD # Importez votre module de gestion de base de données

# Assuming Datas.py contains necessary classes like ObjectId, Compte, etc.
# from Datas import ObjectId, Compte, Operation, TypeOperation, Tier, Echeance, Position, SousCategorie, Beneficiaire, Categorie, TypeBeneficiaire, MoyenPaiement, Placement, HistoriquePlacement

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Money Manager")

        # Initialisation des états de la DB
        self.current_db_path = None
        self.current_account = None # Gardez ceci si vous l'utilisez pour l'état de l'application
        self.pointage_state = {'actif': False, 'solde': 0.0, 'date': '','ops' : set(),'rows' : set(),'suspendu': False}

        # Initialisation pour l'audio (s'assurer que QAudioOutput et QMediaPlayer sont importés de QtMultimedia)
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output) # Associer la sortie audio au lecteur

        self.settings = QSettings("VotreOrganisation", "MoneyManager") # Remplacez par le nom de votre organisation/app

        # Tenter de charger la dernière DB utilisée
        self.load_last_db_path()

        # Configurer l'interface utilisateur
        self.setup_ui()

        # Gérer la logique de démarrage de la DB
        self.initialize_db_on_startup()

        # Maximiser la fenêtre
        self.showMaximized()

    def setup_ui(self):
        # Configurez vos widgets ici (boutons, layouts, etc.)
        layout = QVBoxLayout()

        self.open_button = QPushButton("Ouvrir un fichier .db existant")
        self.open_button.clicked.connect(self.open_file)
        layout.addWidget(self.open_button)

        self.new_db_button = QPushButton("Créer une nouvelle base de données (.db)")
        self.new_db_button.clicked.connect(self.create_new_db_dialog)
        layout.addWidget(self.new_db_button)

        self.test_button = QPushButton("Tester DB (Afficher comptes)")
        self.test_button.clicked.connect(self.test_db_connection)
        layout.addWidget(self.test_button)

        self.setLayout(layout)

        # Mettre à jour le texte des boutons ou l'état de l'interface si une DB est chargée
        self.update_ui_for_db_status()

    def update_ui_for_db_status(self):
        # Cette fonction peut être appelée pour ajuster l'interface utilisateur
        # en fonction de si une DB est chargée ou non.
        if self.current_db_path:
            self.setWindowTitle(f"Money Manager - [{os.path.basename(self.current_db_path)}]")
            # Vous pourriez activer/désactiver certains boutons ici
            # self.test_button.setEnabled(True)
        else:
            self.setWindowTitle("Money Manager - [Aucune base de données chargée]")
            # self.test_button.setEnabled(False)


    def load_last_db_path(self):
        """Charge le chemin de la dernière DB utilisée depuis les paramètres."""
        last_path = self.settings.value("last_db_path", "")
        if last_path and os.path.exists(last_path):
            self.current_db_path = last_path
            print(f"Chargement de la dernière DB : {self.current_db_path}")
        else:
            print("Aucune dernière DB valide trouvée ou le fichier n'existe pas.")

    def save_last_db_path(self, path):
        """Sauvegarde le chemin de la DB actuelle dans les paramètres."""
        self.settings.setValue("last_db_path", path)
        print(f"Chemin de la DB sauvegardé : {path}")

    def initialize_db_on_startup(self):
        """Gère la logique d'initialisation de la DB au démarrage de l'application."""
        if self.current_db_path:
            # Tente de se connecter et d'initialiser les tables pour la DB chargée
            try:
                GestionBD.create_tables(self.current_db_path)
                QMessageBox.information(
                    self,
                    "Base de données chargée",
                    f"La base de données '{os.path.basename(self.current_db_path)}' a été chargée et ses tables vérifiées."
                )
                print(f"DB chargée et initialisée: {self.current_db_path}")
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
        
        # Si aucune DB n'est chargée ou si le chargement a échoué, demander à l'utilisateur
        if not self.current_db_path:
            self.prompt_for_db_action()

        self.update_ui_for_db_status()


    def prompt_for_db_action(self):
        """Demande à l'utilisateur de choisir d'ouvrir ou de créer une DB."""
        reply = QMessageBox.question(
            self,
            "Aucune base de données chargée",
            "Aucune base de données n'a été trouvée ou chargée.\n"
            "Voulez-vous ouvrir une base de données existante ou en créer une nouvelle ?",
            QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Open:
            self.open_file()
        elif reply == QMessageBox.StandardButton.Save:
            self.create_new_db_dialog()
        # Si Cancel, l'application reste ouverte mais sans DB active

    def open_file(self):
        """
        Ouvre un explorateur de fichiers pour sélectionner un fichier .db existant.
        """
        file_filter = "Fichiers de base de données SQLite (*.db);;Tous les fichiers (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier .db",
            "",
            file_filter
        )

        if file_path:
            self.set_current_db(file_path)
        else:
            QMessageBox.information(
                self,
                "Opération annulée",
                "Aucun fichier de base de données sélectionné."
            )
            print("Aucun fichier sélectionné lors de l'ouverture.")

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

    def set_current_db(self, db_path, is_new=False):
        """Définit le chemin de la DB actuelle et initialise/sauvegarde."""
        self.current_db_path = db_path
        self.save_last_db_path(db_path) # Sauvegarder ce chemin comme le dernier utilisé

        # Tenter de créer/initialiser les tables dans la nouvelle DB
        try:
            GestionBD.create_tables(self.current_db_path)
            if is_new:
                QMessageBox.information(
                    self,
                    "Nouvelle base de données",
                    f"La nouvelle base de données '{os.path.basename(self.current_db_path)}' a été créée et ses tables initialisées."
                )
            else:
                 QMessageBox.information(
                    self,
                    "Fichier sélectionné",
                    f"Le fichier de base de données '{os.path.basename(self.current_db_path)}' a été chargé et ses tables vérifiées."
                )
            print(f"DB sélectionnée/créée et initialisée : {self.current_db_path}")
            self.run_echeance_if_db_ready() # Exécute RunEcheance seulement si la DB est prête

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de base de données",
                f"Erreur lors de l'initialisation des tables pour '{os.path.basename(self.current_db_path)}' : {e}\n"
                "Le fichier pourrait être corrompu ou les permissions insuffisantes."
            )
            print(f"Erreur lors de l'initialisation des tables : {e}")
            self.current_db_path = None # Réinitialiser si échec
            self.settings.remove("last_db_path") # Supprimer le chemin invalide
        
        self.update_ui_for_db_status()


    def run_echeance_if_db_ready(self):
        """Exécute RunEcheance seulement si une DB est active."""
        if self.current_db_path:
            try:
                current_date, echeances = GestionBD.GetEcheanceToday(db_path=self.current_db_path)
                GestionBD.RunEcheance(current_date, echeances, db_path=self.current_db_path)
                print("Échéances traitées.")
            except Exception as e:
                print(f"Erreur lors du traitement des échéances : {e}")
                # Vous pourriez afficher un QMessageBox ici si l'erreur est critique

    def test_db_connection(self):
        """
        Teste la connexion à la DB et affiche les comptes.
        """
        if self.current_db_path:
            try:
                # Assurez-vous que GetComptes accepte db_path
                comptes = GestionBD.GetComptes(self.current_db_path)
                if comptes:
                    msg = "Comptes dans la DB :\n"
                    # Assurez-vous que la classe Compte est importée et a des attributs nom et solde
                    for compte in comptes:
                        # Exemple: Vous devrez ajuster selon votre classe Compte réelle
                        # msg += f"- {compte.nom} (Solde: {compte.solde})\n"
                        msg += f"- Compte ID: {compte._id}, Nom: {compte.nom}, Solde: {compte.solde}\n" # Ajustez si GetComptes retourne des tuples
                    QMessageBox.information(self, "Comptes", msg)
                else:
                    QMessageBox.information(self, "Comptes", "Aucun compte trouvé dans la base de données.")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur de connexion DB",
                    f"Impossible de se connecter à la base de données ou de récupérer les comptes : {e}"
                )
                print(f"Erreur de connexion DB : {e}")
        else:
            QMessageBox.warning(
                self,
                "Aucun fichier",
                "Veuillez d'abord sélectionner ou créer un fichier .db."
            )
            print("Aucun fichier .db sélectionné pour le test.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec())