import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from config import *

class UpdateChecker(QDialog):
    def __init__(self, parent=None):
        latest_version = self.get_latest_finao_version()
        if latest_version and latest_version != __version__:
            logger.info(f"New version available: {latest_version}")
            super().__init__(parent)
            self.setWindowTitle("Mise à jour disponible")
            main_layout = QVBoxLayout(self)
            self.message_label = QLabel("Une nouvelle version de Finao est disponible. Voulez-vous mettre à jour?")
            main_layout.addWidget(self.message_label)
            button_layout = QHBoxLayout()
            self.update_button = QPushButton("Mettre à jour")
            self.update_button.clicked.connect(self.update_finao_software)
            self.cancel_button = QPushButton("Annuler")
            self.cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(self.update_button)
            button_layout.addWidget(self.cancel_button)
            main_layout.addLayout(button_layout)
            self.exec()
        else:
            logger.info("No update available.")
            self.close()

    def update_finao_software(self):
        """
        Download the latest release version from the public Finao GitHub repository.
        """
        self.accept()
        # Add your update logic here
        pass

    def get_latest_finao_version(self):
        """
        Fetches the latest release version from the public Finao GitHub repository.
        Returns the version tag as a string or None on failure.
        """
        api_url = 'https://api.github.com/repos/LANCHUT/Finao/releases/latest'
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            latest_version = release_data.get('tag_name')
            return latest_version
        except requests.exceptions.RequestException as e:
            print(f"Error fetching latest version: {e}")
            return None
