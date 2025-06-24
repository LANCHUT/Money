from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGridLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

from GestionBD import GetPerformanceGlobaleData,GetPerformanceByPlacement

import plotly.graph_objects as go
import tempfile
from BaseDialog import BaseDialog

class ShowPerformanceDialog(BaseDialog):
    def __init__(self, parent=None, account_id=None):
        super().__init__(parent)
        self.setWindowTitle("Performances du portefeuille")
        self.account_id = account_id

        main_layout = QHBoxLayout()  # Pour mettre tableau à gauche, graphique à droite
        self.setLayout(main_layout)

        # === Partie gauche (métriques + tableau) ===
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout, 2)

        grid = QGridLayout()
        left_layout.addLayout(grid)

        self.labels = {}
        indicateurs = [
            ("Valorisation actuelle", "valorisation"),
            ("Montant investi", "investi"),
            ("Dons", "dons"),
            ("Ventes", "ventes"),
            ("Intérêts cumulés", "interets"),
            ("Plus-value", "plus_value"),
            ("Performance globale", "performance"),
        ]

        for i, (label_txt, key) in enumerate(indicateurs):
            label_name = QLabel(label_txt + " :")
            label_value = QLabel("0.00 €")
            label_value.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(label_name, i, 0)
            grid.addWidget(label_value, i, 1)
            self.labels[key] = label_value

        # === Tableau des placements ===
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Placement", "Nbre de parts", "Val. Part", "Investissement", "Valorisation", "Intérêts", "Plus-Value", "Performance"
        ])
        left_layout.addWidget(QLabel("\nDétail des placements :"))
        left_layout.addWidget(self.table)

        # === Partie droite : graphique Plotly ===
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        right_layout.addWidget(QLabel("<b>Répartition par placement</b>"))
        self.web_view = QWebEngineView()
        right_layout.addWidget(self.web_view)

        # === Bouton fermeture ===
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        left_layout.addWidget(close_button)

        # === Calcul des données ===
        self.update_performance_data()

    def update_performance_data(self):
        if not self.account_id:
            return

        data = GetPerformanceGlobaleData(self.account_id)

        def format_eur(val):
            return "{:,.2f} €".format(val).replace(",", " ").replace(".", ",")

        # Remplissage des métriques
        self.labels["valorisation"].setText(format_eur(data.get("valo", 0)))
        self.labels["investi"].setText(format_eur(data.get("montant_investissement", 0)))
        self.labels["dons"].setText(format_eur(data.get("don", 0)))
        self.labels["ventes"].setText(format_eur(data.get("vente", 0)))
        self.labels["interets"].setText(format_eur(data.get("cumul_interet", 0)))
        self.labels["plus_value"].setText(format_eur(data.get("plus-value", 0)))
        self.labels["performance"].setText(f'{data.get("perf", 0)} %')

        # === Tableau : afficher les placements ===
        placements = GetPerformanceByPlacement(self.account_id)
        self.table.setRowCount(len(placements))

        for i, p in enumerate(placements):
            self.table.setItem(i, 0, QTableWidgetItem(p.get("nom", "")))
            self.table.setItem(i, 1, QTableWidgetItem(str(p.get("nb_parts", 0))))
            self.table.setItem(i, 2, QTableWidgetItem(format_eur(p.get("val_part", 0))))
            self.table.setItem(i, 3, QTableWidgetItem(format_eur(p.get("investi", 0))))
            self.table.setItem(i, 4, QTableWidgetItem(format_eur(p.get("valorisation", 0))))
            self.table.setItem(i, 5, QTableWidgetItem(format_eur(p.get("interet", 0))))
            self.table.setItem(i, 6, QTableWidgetItem(format_eur(p.get("plus-value", 0))))
            self.table.setItem(i, 7, QTableWidgetItem(f'{p.get("performance", 0)} %'))

        # === Graphique Plotly : donut ===
        self.plot_donut(placements)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def plot_donut(self, placements):
        labels = [p["nom"] for p in placements]
        values = [p["valorisation"] for p in placements]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            texttemplate="%{value:,.2f} €",
            textinfo="label+value+percent"
        )])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            fig.write_html(f.name)
            self.web_view.load(QUrl.fromLocalFile(f.name))
