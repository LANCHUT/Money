import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton


def get_latest_finao_version():
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


class UpdateChecker(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedWidth(300)
        main_layout = QVBoxLayout(self)
        self.message_label = QLabel("A new version of Finao is available. Would you like to update?")
        main_layout.addWidget(self.message_label)
        button_layout = QHBoxLayout()
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_finao_software)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

    def update_finao_software(self):
        """
        Download the latest release version from the public Finao GitHub repository.
        """
        self.accept()
        pass