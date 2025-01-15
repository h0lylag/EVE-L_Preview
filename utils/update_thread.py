from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from Xlib.error import BadDrawable

class UpdateThread(QThread):
    updated = pyqtSignal(QPixmap, int, int)
    error_occurred = pyqtSignal()

    def __init__(self, x11_interface, window_id, window_title, interval=1000):
        super().__init__()
        self.x11_interface = x11_interface
        self.window_id = window_id
        self.window_title = window_title
        self.interval = interval

    def run(self):
        while True:
            try:
                # ✅ Now correctly receives a QImage from x11_interface
                image, original_width, original_height = self.x11_interface.capture_window(int(self.window_id, 16))

                # Scale image to % of the original size
                scale_factor = 0.075  # Assuming `config["settings"]["thumbnail_scaling"]` is 7.5
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                image = image.scaled(new_width, new_height, Qt.KeepAspectRatio)  # ✅ Now works!

                pixmap = QPixmap.fromImage(image)

                # Draw character name on pixmap
                painter = QPainter(pixmap)
                painter.setPen(QColor('white'))
                painter.setFont(QFont('Roboto Mono', 10))
                if " - " in self.window_title:
                    character_name = self.window_title.split(" - ")[-1]
                else:
                    character_name = "Unknown"
                painter.drawText(10, 20, character_name)
                painter.end()

                self.updated.emit(pixmap, new_width, new_height)
            except BadDrawable:
                self.error_occurred.emit()
                break
            except Exception as e:
                print(f"Error updating preview: {e}")
            self
