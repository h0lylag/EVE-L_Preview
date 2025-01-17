from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox
from utils.config import save_config

class ProfilesTab(QWidget):
    def __init__(self, config, parent=None):  # Accept config
        super(ProfilesTab, self).__init__(parent)
        self.config = config  # Store config
        layout = QVBoxLayout()

        self.checkbox1 = QCheckBox("Profiles option 1")
        self.checkbox2 = QCheckBox("Profiles option 2")

        layout.addWidget(self.checkbox1)
        layout.addWidget(self.checkbox2)

        self.setLayout(layout)
