from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from utils.config import save_config

class HotkeysTab(QWidget):
    def __init__(self, config, parent=None):
        super(HotkeysTab, self).__init__(parent)
        self.config = config  # Store config

        layout = QVBoxLayout()

        self.label = QLabel("Enter character names (one per line):")
        self.character_textbox = QTextEdit()
        self.character_textbox.setPlaceholderText("Character Name 1\nCharacter Name 2\nCharacter Name 3")

        # Load stored names from config if available
        stored_names = self.config.get("hotkeys", {}).get("character_list", "")
        self.character_textbox.setPlainText(stored_names)

        layout.addWidget(self.label)
        layout.addWidget(self.character_textbox)
        self.setLayout(layout)

        self.character_textbox.textChanged.connect(self.save_character_list)

    def save_character_list(self):
        """Save the list of character names to config."""
        self.config.setdefault("hotkeys", {})["character_list"] = self.character_textbox.toPlainText()
        save_config(self.config)

    def get_character_list(self):
        """Return character names as a list, stripping whitespace."""
        return [line.strip() for line in self.character_textbox.toPlainText().split("\n") if line.strip()]
