from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox
from utils.config import save_config

class SettingsTab(QWidget):
    def __init__(self, config, parent=None):  # Accept config explicitly
        super(SettingsTab, self).__init__(parent)
        self.config = config  # Store config dictionary

        layout = QVBoxLayout()

        self.checkbox1 = QCheckBox("Settings option 1")
        self.checkbox2 = QCheckBox("Settings option 2")

        layout.addWidget(self.checkbox1)
        layout.addWidget(self.checkbox2)

        self.setLayout(layout)
