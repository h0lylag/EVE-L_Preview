from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from utils.config import save_config

class HotkeysTab(QWidget):
    def __init__(self, config, parent=None):
        super(HotkeysTab, self).__init__(parent)
        self.config = config  # Store config

        layout = QVBoxLayout()

        self.label = QLabel("Enter character names (one per line) in the order you want to cycle through them:")
        self.character_textbox = QTextEdit()
        self.character_textbox.setPlaceholderText("Character Name 1\nCharacter Name 2\nCharacter Name 3")

        # Load stored names from config if available
        stored_chars = self.config.get("hotkeys", {}).get("character_list", {})
        char_list = "\n".join(stored_chars.keys())
        self.character_textbox.setPlainText(char_list)

        layout.addWidget(self.label)
        layout.addWidget(self.character_textbox)
        self.setLayout(layout)

        self.character_textbox.textChanged.connect(self.save_character_list)

    def save_character_list(self):
        """Save the list of character names to config."""
        char_dict = {}
        for line in self.character_textbox.toPlainText().split("\n"):
            if line.strip():
                char_dict[line.strip()] = {}
                
        self.config.setdefault("hotkeys", {})["character_list"] = char_dict
        save_config(self.config)

    def get_character_list(self):
        """Return character names as a list, respecting the order in the text box."""
        return [line.strip() for line in self.character_textbox.toPlainText().split("\n") if line.strip()]
