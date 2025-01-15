from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel, QLineEdit
from utils.config import save_config  # Remove load_config (no need to reload)

class ThumbnailsTab(QWidget):
    def __init__(self, config, parent=None):  # ✅ Accept config explicitly
        super(ThumbnailsTab, self).__init__(parent)
        self.config = config  # ✅ Store config

        layout = QVBoxLayout()

        self.enable_borders_checkbox = QCheckBox("Enable Borders")
        self.enable_borders_checkbox.setChecked(self.config["settings"]["enable_borders"])
        self.enable_borders_checkbox.stateChanged.connect(self.toggle_borders)

        self.active_border_color_label = QLabel("Active Client Border Color:")
        self.active_border_color_input = QLineEdit(self.config["settings"]["active_border_color"])

        self.inactive_border_color_label = QLabel("Inactive Client Border Color:")
        self.inactive_border_color_input = QLineEdit(self.config["settings"]["inactive_border_color"])

        layout.addWidget(self.enable_borders_checkbox)
        layout.addWidget(self.active_border_color_label)
        layout.addWidget(self.active_border_color_input)
        layout.addWidget(self.inactive_border_color_label)
        layout.addWidget(self.inactive_border_color_input)

        self.setLayout(layout)

        self.active_border_color_input.editingFinished.connect(self.update_active_border_color)
        self.inactive_border_color_input.editingFinished.connect(self.update_inactive_border_color)

    def toggle_borders(self, state):
        self.config["settings"]["enable_borders"] = bool(state)
        save_config(self.config)

    def update_active_border_color(self):
        color = self.active_border_color_input.text()
        if self.is_valid_hex_color(color):
            self.config["settings"]["active_border_color"] = color
            save_config(self.config)

    def update_inactive_border_color(self):
        color = self.inactive_border_color_input.text()
        if self.is_valid_hex_color(color):
            self.config["settings"]["inactive_border_color"] = color
            save_config(self.config)

    def is_valid_hex_color(self, color):
        if color.startswith('#') and len(color) == 7:
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                pass
        return False
