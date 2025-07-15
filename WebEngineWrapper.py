import sys
import json

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
import plotly.graph_objects as go

# -----------------------
# Sunburst generation
# -----------------------
def sunburst_chart(data_raw):
    processed_data = []
    for entry in data_raw:
        new_entry = entry.copy()
        if new_entry["montant"] < 0:
            new_entry["type_flux"] = "Revenus"
            new_entry["montant"] = round(abs(new_entry["montant"]), 2)
        else:
            new_entry["type_flux"] = "Dépenses"
        processed_data.append(new_entry)

    sunburst_labels = []
    sunburst_parents = []
    sunburst_values = []
    sunburst_ids = []
    sunburst_colors = []
    aggregated_totals = {}
    added_ids_to_sunburst_lists = set()

    COLOR_DEPENSES_BASE = 'rgb(255, 99, 71)'
    COLOR_REVENUS_BASE = 'rgb(60, 179, 113)'

    for entry in processed_data:
        type_flux = entry["type_flux"]
        compte = entry["compte"]
        categorie = entry["categorie"]
        sous_cat = entry["sous_cat"]
        montant = round(entry["montant"], 2)

        type_flux_id = type_flux
        compte_id = f"{type_flux_id}_{compte}"
        categorie_id = f"{compte_id}_{categorie}"
        sous_cat_id = f"{categorie_id}_{sous_cat}"

        aggregated_totals[type_flux_id] = aggregated_totals.get(type_flux_id, 0) + montant
        aggregated_totals[compte_id] = aggregated_totals.get(compte_id, 0) + montant
        aggregated_totals[categorie_id] = aggregated_totals.get(categorie_id, 0) + montant

        if sous_cat_id not in added_ids_to_sunburst_lists:
            sunburst_ids.append(sous_cat_id)
            sunburst_labels.append(f"{sous_cat} ({montant}€)")
            sunburst_parents.append(categorie_id)
            sunburst_values.append(montant)
            sunburst_colors.append(COLOR_DEPENSES_BASE if type_flux == "Dépenses" else COLOR_REVENUS_BASE)
            added_ids_to_sunburst_lists.add(sous_cat_id)

    unique_categories = set((e["type_flux"], e["compte"], e["categorie"]) for e in processed_data)
    for type_flux, compte, categorie in unique_categories:
        type_flux_id = type_flux
        compte_id = f"{type_flux_id}_{compte}"
        categorie_id = f"{compte_id}_{categorie}"
        if categorie_id not in added_ids_to_sunburst_lists:
            sunburst_ids.append(categorie_id)
            sunburst_labels.append(categorie)
            sunburst_parents.append(compte_id)
            sunburst_values.append(aggregated_totals.get(categorie_id, 0))
            sunburst_colors.append(COLOR_DEPENSES_BASE if type_flux == "Dépenses" else COLOR_REVENUS_BASE)
            added_ids_to_sunburst_lists.add(categorie_id)

    unique_comptes = set((e["type_flux"], e["compte"]) for e in processed_data)
    for type_flux, compte in unique_comptes:
        type_flux_id = type_flux
        compte_id = f"{type_flux_id}_{compte}"
        if compte_id not in added_ids_to_sunburst_lists:
            sunburst_ids.append(compte_id)
            sunburst_labels.append(compte)
            sunburst_parents.append(type_flux_id)
            sunburst_values.append(aggregated_totals.get(compte_id, 0))
            sunburst_colors.append(COLOR_DEPENSES_BASE if type_flux == "Dépenses" else COLOR_REVENUS_BASE)
            added_ids_to_sunburst_lists.add(compte_id)

    unique_types_flux = set(e["type_flux"] for e in processed_data)
    for type_flux in unique_types_flux:
        type_flux_id = type_flux
        if type_flux_id not in added_ids_to_sunburst_lists:
            sunburst_ids.append(type_flux_id)
            sunburst_labels.append(type_flux)
            sunburst_parents.append("")
            sunburst_values.append(aggregated_totals.get(type_flux_id, 0))
            sunburst_colors.append(COLOR_DEPENSES_BASE if type_flux == "Dépenses" else COLOR_REVENUS_BASE)
            added_ids_to_sunburst_lists.add(type_flux_id)

    fig = go.Figure(go.Sunburst(
        ids=sunburst_ids,
        labels=sunburst_labels,
        parents=sunburst_parents,
        values=sunburst_values,
        branchvalues="total",
        hovertemplate='<b>%{label}</b><br>Montant: %{value}€<extra></extra>',
        marker=dict(colors=sunburst_colors)
    ))
    fig.update_layout(
        title="Dépenses et Revenus par Type, Compte, Catégorie et Sous-catégorie",
        height=800,
        width=800,
        margin=dict(t=30, l=0, r=0, b=0)
    )
    return fig

# -----------------------
# WebChannel Bridge
# -----------------------
class JsBridge(QObject):
    clicked = pyqtSignal(str)

    @pyqtSlot(str)
    def handleClick(self, data):
        print(f"Clicked: {data}")
        self.clicked.emit(data)

# -----------------------
# Main Window
# -----------------------
class MainWindow(QMainWindow):
    def handle_console_message(self, level, message, line, source_id):
        print(f"JS Console: {message} (Line {line})")

    def __init__(self):
        super().__init__()
        self.view = QWebEngineView()
        self.bridge = JsBridge()
        self.setWindowTitle("PyQt6 + Plotly Sunburst Clickable")
        self.setGeometry(100, 100, 1000, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.init_main_tab()
        self.view.page().consoleMessage = self.handle_console_message

    def init_main_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        channel = QWebChannel()
        self.bridge = JsBridge()
        channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(channel)

        self.bridge.clicked.connect(self.open_detail_tab)

        data_raw = [
            {"montant": -1500, "compte": "Compte Principal", "categorie": "Salaire", "sous_cat": "Régulier"},
            {"montant": -500, "compte": "Compte Épargne", "categorie": "Investissement", "sous_cat": "Dividendes"},
            {"montant": 80, "compte": "Compte Courant", "categorie": "Alimentation", "sous_cat": "Supermarché"},
            {"montant": 25, "compte": "Compte Courant", "categorie": "Alimentation", "sous_cat": "Restaurant"},
            {"montant": 50, "compte": "Carte Crédit", "categorie": "Transport", "sous_cat": "Essence"},
            {"montant": 120, "compte": "Compte Courant", "categorie": "Divertissement", "sous_cat": "Cinéma"},
            {"montant": 30, "compte": "Compte Principal", "categorie": "Divertissement", "sous_cat": "Jeux"},
            {"montant": -200, "compte": "Compte Courant", "categorie": "Remboursement", "sous_cat": "Ami"}
        ]

        fig = sunburst_chart(data_raw)
        fig_json = json.dumps(fig.to_plotly_json())

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        </head>
        <body>
            <div id="plot"></div>
            <script>
                console.log(document.documentElement.outerHTML);
                var fig = {fig_json};
                Plotly.newPlot('plot', fig.data, fig.layout);
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.bridge = channel.objects.bridge;
                }});
                document.getElementById('plot').on('plotly_click', function(data) {{
                    if(data.points.length > 0){{
                        var clicked_id = data.points[0].id;
                        window.bridge.handleClick(clicked_id);
                    }}
                }});
            </script>
        </body>
        </html>
        """

        self.view.setHtml(html_content)
        layout.addWidget(self.view)
        self.tabs.addTab(tab, "Sunburst Chart")

    @pyqtSlot(str)
    def open_detail_tab(self, data):
        print("test")
        tab = QWidget()
        layout = QVBoxLayout(tab)
        label = QLabel(f"Clicked on: {data}")
        layout.addWidget(label)
        self.tabs.addTab(tab, f"Détails: {data.split('_')[-1]}")
        self.tabs.setCurrentWidget(tab)

# -----------------------
# Main Execution
# -----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
