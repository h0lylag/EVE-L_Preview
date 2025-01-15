from PyQt5.QtCore import QTimer, QObject
from utils.window_preview import WindowPreview

class WindowManager(QObject):  # ✅ Inherit from QObject for Qt threading safety
    def __init__(self, x11_interface, config):
        super().__init__()
        self.x11_interface = x11_interface
        self.config = config
        self.previews = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_previews)
        self.timer.start(1000)

    def update_previews(self):
        window_list = self.x11_interface.list_windows()
        eve_windows = [(line.split()[0], " ".join(line.split()[3:])) for line in window_list if "EVE - " in line]

        current_ids = {preview.window_id for preview in self.previews}
        new_windows = [(window_id, window_title) for window_id, window_title in eve_windows if window_id not in current_ids]
        closed_windows = [preview for preview in self.previews if preview.window_id not in {window_id for window_id, _ in eve_windows}]

        for window_id, window_title in new_windows:
            preview = WindowPreview(self.x11_interface, window_id, window_title, self.previews, self.config, self)
            preview.show()
            self.previews.append(preview)

        for preview in closed_windows:
            self.previews.remove(preview)
            preview.close()
