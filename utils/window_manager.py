from PyQt5.QtCore import QTimer, QObject
from utils.window_preview import WindowPreview
from utils.window_border import BorderWindow
import logging

class WindowManager(QObject):
    def __init__(self, x11_interface, config, hotkey_manager=None):
        super().__init__()
        self.x11_interface = x11_interface
        self.config = config
        self.hotkey_manager = hotkey_manager  # Add hotkey_manager
        self.previews = []
        self.last_active_window_id = None  # Track active window
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_previews)
        self.timer.start(1000)
        self.active_border = BorderWindow(config)

    def update_previews(self):
        window_list = self.x11_interface.list_windows()
        eve_windows = [(line.split()[0], " ".join(line.split()[3:])) for line in window_list if "EVE - " in line]

        current_ids = {preview.window_id for preview in self.previews}
        new_windows = [(window_id, window_title) for window_id, window_title in eve_windows if window_id not in current_ids]
        closed_windows = [preview for preview in self.previews if preview.window_id not in {window_id for window_id, _ in eve_windows}]

        for window_id, window_title in new_windows:
            preview = WindowPreview(self.x11_interface, window_id, window_title, self.previews, self.config, self, self.hotkey_manager)
            preview.show()
            self.previews.append(preview)

        for preview in closed_windows:
            # Check if this is the active window before removing it
            if self.last_active_window_id == preview.window_id:
                # Hide the border window when active client closes
                self.active_border.hide()
                self.last_active_window_id = None
                
            self.previews.remove(preview)
            preview.close()

    def set_last_active_client(self, window_id):
        """Set the last active client and update border."""
        logging.debug(f"Setting last active client: {window_id}")
        self.last_active_window_id = window_id
        
        # Find the preview window matching this ID
        for preview in self.previews:
            if preview.window_id == window_id:
                # Move border window to surround this preview
                self.active_border.follow(preview)
                break

    def refresh_borders(self):
        """Update borders on all preview windows."""
        for preview in self.previews:
            preview.update_border()

    def get_last_active_client(self):
        """Returns the last active window ID."""
        return self.last_active_window_id
