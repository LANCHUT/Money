from PyQt6.QtWidgets import QTableWidgetItem,QDateEdit
from PyQt6.QtCore import QDate,Qt
from PyQt6.QtGui import QKeyEvent

class DateTableWidgetItem(QTableWidgetItem):
    def __init__(self, date_input):
        # Détecter si c'est un int ou un str
        if isinstance(date_input, int):
            # Transformer l'int en QDate
            date_str = str(date_input)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            self.date = QDate(year, month, day)
            # Afficher au format lisible dans la cellule
            display_text = self.date.toString("dd/MM/yyyy")
            super().__init__(display_text)
        elif isinstance(date_input, str):
            self.date = QDate.fromString(date_input, "dd/MM/yyyy")
            super().__init__(date_input)
        else:
            raise ValueError("DateTableWidgetItem doit recevoir un int (YYYYMMDD) ou une str ('dd/MM/yyyy').")

    def __lt__(self, other):
        if isinstance(other, DateTableWidgetItem):
            return self.date < other.date
        return super().__lt__(other)
    
class CustomDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self.setDisplayFormat("dd/MM/yyyy")

    def keyPressEvent(self, event: QKeyEvent):
        current_date = self.date()
        key = event.key()
        if key == Qt.Key.Key_PageUp:
            self.setDate(current_date.addMonths(1))
        elif key == Qt.Key.Key_PageDown:
            self.setDate(current_date.addMonths(-1))
        elif key in [Qt.Key.Key_Up,Qt.Key.Key_Plus]:
            self.setDate(current_date.addDays(1))
        elif key in [Qt.Key.Key_Down,Qt.Key.Key_Minus]:
            self.setDate(current_date.addDays(-1))
        else:
            super().keyPressEvent(event)
