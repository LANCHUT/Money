import sys
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt

class FenetreFiltres(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Application de Filtres")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #2b2b2b; color: #f0f0f0;") # Fond sombre pour la fenêtre

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.btn_appliquer = QPushButton("Appliquer les filtres")
        self.btn_reinitialiser = QPushButton("Réinitialiser les filtres")
        
        self.btn_appliquer.clicked.connect(lambda: print("Filtres appliqués"))
        self.btn_reinitialiser.clicked.connect(lambda: print("Filtres réinitialisés"))

        top_buttons_layout.addWidget(self.btn_appliquer)
        top_buttons_layout.addWidget(self.btn_reinitialiser)
        top_buttons_layout.setContentsMargins(0, 10, 20, 10)
        
        main_layout.addLayout(top_buttons_layout)
        
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)

        self.btn_ajouter_transaction = QPushButton("Ajouter une transaction")
        self.btn_commencer_pointage = QPushButton("Commencer le pointage")

        self.btn_ajouter_transaction.clicked.connect(lambda: print("Ajouter transaction"))
        self.btn_commencer_pointage.clicked.connect(lambda: print("Commencer pointage"))

        bottom_buttons_layout.addWidget(self.btn_ajouter_transaction)
        bottom_buttons_layout.addWidget(self.btn_commencer_pointage)
        bottom_buttons_layout.setContentsMargins(0, 10, 0, 10)

        main_layout.addLayout(bottom_buttons_layout)
        
        self.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    qss = """
    /* Style général pour tous les QPushButton */
    QPushButton {
        background-color: #3a3a3a; /* Fond gris très foncé, similaire à votre image */
        color: #e0e0e0; /* Texte gris clair */
        border: 1px solid #4a4a4a; /* Bordure par défaut très fine et légèrement plus claire */
        border-radius: 5px; /* Coins légèrement arrondis */
        padding: 8px 15px; /* Espacement interne */
        font-size: 14px;
        min-width: 120px; /* Taille minimale pour qu'ils soient tous similaires */
        margin: 5px; /* Petite marge entre les boutons */
    }

    /* Effet au survol (hover) */
    QPushButton:hover {
        background-color: #454545; /* Légèrement plus clair au survol */
        color: #ffffff; /* Texte devient blanc pur */
        border: 2px solid #0096FF; /* <<=== ICI LA BORDURE EN SURBRILLANCE ===>> */
        box-shadow: 0 0 8px rgba(0, 150, 255, 0.6); /* Lueur bleue subtile (peut être supprimée si vous préférez juste la bordure) */
    }

    /* Effet quand pressé */
    QPushButton:pressed {
        background-color: #2f2f2f; /* Devient un peu plus foncé */
        color: #cccccc; /* Texte légèrement estompé */
        border: 1px solid #3a3a3a; /* Bordure s'assombrit (revient à la taille/couleur par défaut ou proche) */
        box-shadow: none; /* Enlève l'ombre pour un effet "enfoncé" */
    }

    /* Style pour les boutons désactivés */
    QPushButton:disabled {
        background-color: #303030;
        color: #808080;
        border: 1px solid #404040;
        box-shadow: none;
    }
    """
    app.setStyleSheet(qss)

    fenetre = FenetreFiltres()
    fenetre.show()
    sys.exit(app.exec())