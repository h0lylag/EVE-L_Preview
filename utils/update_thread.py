from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from Xlib.error import BadDrawable
import logging

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
                # Only log if debug level is enabled to reduce overhead
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.debug(f"Updating preview for window: {self.window_id}")
                
                image, original_width, original_height = self.x11_interface.capture_window(int(self.window_id, 16))
                
                # Skip if image capture failed
                if image is None:
                    logging.warning(f"Skipping update: Window {self.window_id} capture failed.")
                    self.error_occurred.emit()
                    break

                # Convert to pixmap without drawing character name
                pixmap = QPixmap.fromImage(image)

                self.updated.emit(pixmap, original_width, original_height)

            except BadDrawable:
                logging.error(f"BadDrawable error for window {self.window_id}. Stopping thread.")
                self.error_occurred.emit()
                break

            except Exception as e:
                logging.error(f"Error updating preview for {self.window_id}: {e}")

            self.msleep(self.interval)
