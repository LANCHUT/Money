from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGridLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

from database.gestion_bd import GetPerformanceGlobaleData,GetPerformanceByPlacement

import plotly.graph_objects as go
import tempfile
from .BaseDialog import BaseDialog

def align(item: QTableWidgetItem,alignement:Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> QTableWidgetItem:
    item.setTextAlignment(alignement)
    return item


def table_style(table:QTableWidget):
    table.setStyleSheet("""
            QHeaderView::section{
                border: 1px solid white;
                padding: 4px;
                font-weight: bold;}
            QTableWidget::item{
                padding-left: 6px;
                padding-right: 6px;}""")

class ShowPerformanceDialog(BaseDialog):
    def __init__(self, parent=None, account_id=None):
        super().__init__(parent)
        self.resize(1200, 700)
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
            ("Pertes", "pertes"),
            ("Intérêts cumulés", "interets"),
            ("Plus-value", "plus_value"),
            ("Frais", "frais"),
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
        table_style(self.table)
        self.table.resizeColumnsToContents()
        left_layout.addWidget(QLabel("\nDétail des placements :"))
        left_layout.addWidget(self.table)

        # === Partie droite : graphique Plotly ===
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

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

        def format_eur(val,is_nb_part = 0):
            if is_nb_part:
                return "{:,.4f} €".format(val).replace(",", " ").replace(".", ",")
            else:
                return "{:,.2f} €".format(val).replace(",", " ").replace(".", ",")

        # Remplissage des métriques
        self.labels["valorisation"].setText(format_eur(data.get("valo", 0)))
        self.labels["investi"].setText(format_eur(data.get("montant_investissement", 0)))
        self.labels["dons"].setText(format_eur(data.get("don", 0)))
        self.labels["ventes"].setText(format_eur(data.get("vente", 0)))
        self.labels["pertes"].setText(format_eur(data.get("perte", 0)))
        self.labels["interets"].setText(format_eur(data.get("cumul_interet", 0)))
        self.labels["plus_value"].setText(format_eur(data.get("plus-value", 0)))
        self.labels["frais"].setText(format_eur(data.get("frais", 0)))
        self.labels["performance"].setText(f'{data.get("perf", 0)} %')

        # === Tableau : afficher les placements ===
        placements = GetPerformanceByPlacement(self.account_id)
        self.table.setRowCount(len(placements))

        for i, p in enumerate(placements):
            self.table.setItem(i, 0, align(QTableWidgetItem(p.get("nom", ""))))
            self.table.setItem(i, 1, align(QTableWidgetItem(str(f"{float(p.get('nb_parts', 0)):,.4f}".replace(",", " ").replace(".", ","))),Qt.AlignmentFlag.AlignRight))
            self.table.setItem(i, 2, align(QTableWidgetItem(format_eur(p.get("val_part", 0),1)),Qt.AlignmentFlag.AlignRight))
            self.table.setItem(i, 3, align(QTableWidgetItem(format_eur(p.get("investi", 0))),Qt.AlignmentFlag.AlignRight))
            self.table.setItem(i, 4, align(QTableWidgetItem(format_eur(p.get("valorisation", 0))),Qt.AlignmentFlag.AlignRight))
            self.table.setItem(i, 5, align(QTableWidgetItem(format_eur(p.get("interet", 0))),Qt.AlignmentFlag.AlignRight))
            self.table.setItem(i, 6, align(QTableWidgetItem(format_eur(p.get("plus-value", 0))),Qt.AlignmentFlag.AlignRight))
            self.table.setItem(i, 7, align(QTableWidgetItem(f'{p.get("performance", 0)} %'),Qt.AlignmentFlag.AlignRight))

        # === Graphique Plotly : donut ===
        self.plot_donut(placements)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def plot_donut(self, placements):
        labels = [p["nom"] for p in placements]
        values = [p["valorisation"] for p in placements]

        # Format des valeurs avec des espaces insécables pour les milliers
        formatted_values = [
            f"{v/1000:,.1f}".replace(",", " ").replace(".", ",") + " k€" if v >= 1000
            else f"{v:,.2f}".replace(",", " ").replace(".", ",") + " €"
            for v in values
        ]  # note: espace insécable = U+202F
        bg_color = "#1e1e1e"
        font_color = "#ffffff"

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            textinfo="label+percent",  # on affiche la valeur formatée via texttemplate
            texttemplate="%{customdata}<br>%{percent:.2%}",
            customdata=formatted_values
        )])

        # Personnalisation : titre, marges, légende et fond
        fig.update_layout(
            title=dict(
                text="Répartition par placement",
                y=0.94,  # Plus bas que la position par défaut (~0.95)
                x=0.5,   # Centré horizontalement
                xanchor='center',
                yanchor='top'
            ),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(
                orientation='h',
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color,
            font=dict(color=font_color),   # Fond général du graphique
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
            html = fig.to_html(full_html=True)
            # Injecte style CSS pour changer la couleur de fond du body
            html = html.replace(
                "<head>",
                "<head><style>body { background-color: #1e1e1e; margin: 0; }</style>"
            )
            f.write(html)
            self.web_view.load(QUrl.fromLocalFile(f.name))
