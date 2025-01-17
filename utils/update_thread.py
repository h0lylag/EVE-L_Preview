from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from Xlib.error import BadDrawable
import logging
import threading

# Enable logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class UpdateThread(QThread):
    updated = pyqtSignal(QPixmap, int, int)
    error_occurred = pyqtSignal()

    def __init__(self, x11_interface, window_id, window_title, interval=1000):
        super().__init__()
        self.x11_interface = x11_interface
        self.window_id = window_id
        self.window_title = window_title
        self.interval = interval
        self.lock = threading.Lock()  #Prevents race conditions with Xlib

    def run(self):
        while True:
            try:
                logging.debug(f"Updating preview for window: {self.window_id}")
                
                with self.lock:  # Ensure only one thread accesses X11 at a time
                    image, original_width, original_height = self.x11_interface.capture_window(int(self.window_id, 16))
                
                # Check if image capture failed
                if image is None:
                    logging.warning(f"Skipping update: Window {self.window_id} capture failed.")
                    self.error_occurred.emit()
                    break

                scale_factor = 0.060
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                image = image.scaled(new_width, new_height, Qt.KeepAspectRatio)

                pixmap = QPixmap.fromImage(image)

                # Draw character name
                painter = QPainter(pixmap)
                painter.setPen(QColor('white'))
                painter.setFont(QFont('Roboto Mono', 10))
                character_name = self.window_title.split(" - ")[-1] if " - " in self.window_title else "Unknown"
                painter.drawText(10, 20, character_name)
                painter.end()

                self.updated.emit(pixmap, new_width, new_height)

            except BadDrawable:
                logging.error(f"BadDrawable error for window {self.window_id}. Stopping thread.")
                self.error_occurred.emit()
                break

            except Exception as e:
                logging.error(f"Error updating preview for {self.window_id}: {e}")

            self.msleep(self.interval)
