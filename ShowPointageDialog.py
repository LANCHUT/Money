from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox,QTableWidget
from PyQt6.QtCore import QDate,Qt
from DateTableWidgetItem import CustomDateEdit
from GestionBD import InsertHistoriquePointage, UpdateBqOperation

def show_pointage_dialog(parent, dernier_solde, derniere_date):
    # Convertir "YYYYMMDD" en QDate et format lisible
    year = int(derniere_date[:4])
    month = int(derniere_date[4:6])
    day = int(derniere_date[6:8])
    derniere_date_qdate = QDate(year, month, day)
    formatted_date = derniere_date_qdate.toString("dd/MM/yyyy")
    dialog = QDialog(parent)
    dialog.setWindowTitle("Débuter un pointage")
    layout = QVBoxLayout(dialog)

    layout.addWidget(QLabel(f"Dernier solde connu : {dernier_solde:.2f} € (au {formatted_date})"))

    date_edit = CustomDateEdit()
    date_edit.setDate(derniere_date_qdate.addMonths(1))  # +1 mois

    solde_input = QLineEdit()
    solde_input.setPlaceholderText("Solde relevé")

    layout.addWidget(QLabel("Nouvelle date de pointage :"))
    layout.addWidget(date_edit)
    layout.addWidget(QLabel("Solde relevé :"))
    layout.addWidget(solde_input)

    button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    layout.addWidget(button_box)

    result = {}

    def accepter():
        try:
            result['solde'] = float(solde_input.text().replace(" ","").replace(",","."))
            result['date'] = date_edit.date().toString("yyyyMMdd")
            dialog.accept()
        except ValueError:
            QMessageBox.warning(parent, "Erreur", "Veuillez entrer un solde valide.")

    button_box.accepted.connect(accepter)
    button_box.rejected.connect(dialog.reject)

    if dialog.exec():
        return result
    else:
        return None


def handle_bq_click(row, column, table: QTableWidget, pointage_state, parent, ui_parent):
    if not pointage_state['actif'] or column != 9 or pointage_state["suspendu"]:
        return

    bq_item = table.item(row, 9)
    op_id_item = table.item(row, 0)
    if not op_id_item:
        return

    if bq_item.text() == 'R':
        return

    op_id = op_id_item.data(Qt.ItemDataRole.UserRole)
    is_already_pointed = bq_item.text() == 'P'

    debit_item = table.item(row, 12)
    credit_item = table.item(row, 13)

    montant = 0
    if debit_item and debit_item.text():
        montant = float(debit_item.text().replace("€", "").replace(",", ".").replace(" ", ""))
    elif credit_item and credit_item.text():
        montant = float(credit_item.text().replace("+", "").replace(" ", "").replace(",", ".").replace("€", ""))
    
    if is_already_pointed:
        # Dépointage
        pointage_state['solde'] -= montant
        pointage_state['ops'].discard(op_id)
        pointage_state['rows'].discard(row)
        pointage_state['somme_pointees'] -= montant
        bq_item.setText('')
    else:
        # Pointage
        pointage_state['solde'] += montant
        pointage_state['ops'].add(op_id)
        pointage_state['rows'].add(row)
        pointage_state['somme_pointees'] += montant
        bq_item.setText('P')

    # Mise à jour de l’affichage
    current = pointage_state['solde']
    target = pointage_state['target']
    delta = round(target - current,2)

    ui_parent.end_pointage_btn.setEnabled(abs(delta) < 0.01)

    ui_parent.pointage_info_label.setText(
        f"Dernier relevé : {target:.2f} € – Somme pointées : {pointage_state['somme_pointees']:.2f} € – Écart : {delta:.2f} €"
    )


def finalize_pointage(pointage_state, solde_cible,date,parent):
    delta = pointage_state['solde'] - solde_cible
    if abs(delta) < 0.01:
        QMessageBox.information(parent, "Pointage réussi", "Le solde est exact. Aucune différence détectée.")
    else:
        QMessageBox.warning(parent, "Écart détecté", f"Attention : il reste un écart de {delta:.2f} €")

    InsertHistoriquePointage(parent.current_account,date,solde_cible)
    for operation_id in pointage_state['ops']:
        UpdateBqOperation(operation_id)    

    pointage_state['actif'] = False
    pointage_state['solde'] = 0
    pointage_state['date'] = ""
    pointage_state['rows'] = set()
    pointage_state['ops'] = set()
    pointage_state['somme_pointees'] = 0

def cancel_pointage(pointage_state,table:QTableWidget):
    for row in pointage_state['rows']:
        bq_item = table.item(row, 9)
        bq_item.setText('')
    pointage_state['actif'] = False
    pointage_state['solde'] = 0
    pointage_state['rows'] = set()
    pointage_state['ops'] = set()
    pointage_state['somme_pointees'] = 0
    pointage_state['date'] = ""