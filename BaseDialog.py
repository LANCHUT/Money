from PyQt6.QtWidgets import QDialog
from PyQt6.QtGui import QGuiApplication

class BaseDialog(QDialog):
    def center_and_resize(self, width=600, height=400):
        self.resize(width, height)
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)