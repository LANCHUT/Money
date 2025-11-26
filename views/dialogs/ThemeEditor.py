from PyQt6.QtWidgets import (
    QPushButton, QFormLayout, QColorDialog, QInputDialog,
    QVBoxLayout, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import sqlite3
from models.theme import Theme
from database.gestion_bd import GetTheme
from views.dialogs.BaseDialog import BaseDialog



class ThemeEditor(BaseDialog):

    def update_button_preview(self, attr):
            val = getattr(self.theme, attr, None)
            btn = self.buttons[attr]

            if val is None:
                btn.setText("Choisir")
                return

            # Pour police / taille
            if attr in ("font_family", "font_size"):
                btn.setText(str(val))
            else:
                # Pour les couleurs
                btn.setStyleSheet(f"background:{val}; color:white;")

    def save(self):
        try:
            conn = sqlite3.connect(self.db)
            c = conn.cursor()

            # S'assure que la ligne existe
            c.execute("SELECT COUNT(*) FROM theme")
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO theme (id) VALUES (1)")

            # Génère colonne = ? pour chaque attribut
            cols = ", ".join([f"{attr}=?" for attr in self.attributes])
            values = [getattr(self.theme, attr) for attr in self.attributes]

            query = f"UPDATE theme SET {cols} WHERE id=1"
            c.execute(query, values)

            conn.commit()
            conn.close()
            self.accept()

        except Exception as e:
            print("Erreur lors de la sauvegarde du thème :", e)

    def pick_value(self, attr):
        btn = self.buttons[attr]

        # Gestion police / taille de police
        if attr in ("font_family", "font_size"):
            if attr == "font_size":
                value, ok = QInputDialog.getInt(
                    self,
                    "Taille de police",
                    "Taille (px) :",
                    int(getattr(self.theme, attr)),
                    6,
                    50
                )
            else:
                value, ok = QInputDialog.getText(
                    self,
                    "Famille de police",
                    "Nom de la police :",
                    text=str(getattr(self.theme, attr))
                )

            if ok:
                setattr(self.theme, attr, str(value))
                btn.setText(str(value))
            return

        # ----- CHOIX COULEUR AVEC COULEUR ACTUELLE -----
        current_color = getattr(self.theme, attr)
        color = QColorDialog.getColor(QColor(current_color), self, "Choisir une couleur")

        if color.isValid():
            setattr(self.theme, attr, color.name())
            btn.setStyleSheet(f"background:{color.name()}; color:white;")

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Personnalisation du thème")
        self.setFixedSize(480, 650)  # taille fixe de la fenêtre

        # ----- LAYOUT PRINCIPAL -----
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # ----- ZONE SCROLLABLE -----
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)

        main_layout.addWidget(scroll_area)

        # Charge le thème
        self.theme = GetTheme()

        # Liste des attributs
        self.attributes = {
            "window_bg": "Fond de l'application",
            "text_color": "Couleur de la police",
            "button_bg": "Bouton (normal) - fond",
            "button_fg": "Bouton (normal) - texte",
            "button_border": "Bouton (normal) - bordure",
            "button_hover_bg": "Bouton (survol) - fond",
            "button_hover_border": "Bouton (survol) - bordure",
            "button_pressed_bg": "Bouton (appuyé) - fond",
            "button_pressed_border": "Bouton (appuyé) - bordure",
            "button_disabled_bg": "Bouton (désactivé) - fond",
            "button_disabled_fg": "Bouton (désactivé) - texte",
            "button_disabled_border": "Bouton (désactivé) - bordure",
            "tab_selected_bg": "Onglet sélectionné - fond",
            "tab_selected_fg": "Onglet sélectionné - texte",
            "font_family": "Police (famille)",
            "font_size": "Police (taille px)",
            "header_tab_bg": "En-tête tableau - fond",
            "header_tab_fg": "En-tête tableau - texte",
            "header_tab_border": "En-tête tableau - bordure",
            "positive_color": "Couleur de solde positif",
            "negative_color": "Couleur de solde négatif",
            "line_color": "Couleur courbe placements",
            "row_selected_bg": "Ligne selectionnée - fond",
            "row_selected_fg": "Ligne selectionnée - texte",
            "odd_line_bg": "Lignes paires - fond"
        }

        # Création des boutons dans le scroll
        self.buttons = {}
        for attr, label in self.attributes.items():
            btn = QPushButton("Choisir")
            self.buttons[attr] = btn
            self.update_button_preview(attr)
            btn.clicked.connect(lambda _, a=attr: self.pick_value(a))
            form_layout.addRow(label, btn)

        # ----- BOUTON FIXE EN BAS -----
        save_button = QPushButton("Enregistrer le thème")
        save_button.setFixedHeight(60)
        save_button.clicked.connect(self.save)

        main_layout.addWidget(save_button)
