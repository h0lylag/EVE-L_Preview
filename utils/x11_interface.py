import subprocess
import logging
import threading
from Xlib import X, display
from PyQt5.QtGui import QImage

# Enable logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class X11Interface:
    def __init__(self):
        self.display = display.Display()
        self.lock = threading.Lock()  # Ensure X11 operations are thread-safe

    def capture_window(self, window_id):
        """Safely capture the window image, preventing crashes."""
        logging.debug(f"Attempting to capture window: {window_id}")
        with self.lock:  # Use a threading lock to prevent race conditions
            try:
                window = self.display.create_resource_object('window', window_id)
                geom = window.get_geometry()
                width, height = geom.width, geom.height

                # Ensure the window exists before capturing
                if width == 0 or height == 0:
                    logging.error(f"Window {window_id} has zero dimensions, skipping capture.")
                    return None, 0, 0

                raw = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)
                image = QImage(raw.data, width, height, QImage.Format_RGB32)

                logging.debug(f"Successfully captured window {window_id} ({width}x{height})")
                return image, width, height

            except Exception as e:
                logging.error(f"Failed to capture window {window_id}: {e}")
                return None, 0, 0  # Return None instead of crashing

    def focus_and_raise_window(self, window_id):
        """Bring a window to the front."""
        logging.debug(f"Attempting to bring window {window_id} to the front...")
        try:
            wmctrl_command = ['wmctrl', '-i', '-a', window_id]
            subprocess.call(wmctrl_command)
            logging.info(f"Window {window_id} successfully brought to front.")
            return True
        except Exception as e:
            logging.error(f"Error bringing window {window_id} to front: {e}")
            return False

    def list_windows(self):
        """List all open windows."""
        with self.lock:  # Lock X11 operations to avoid thread conflicts
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            logging.debug(f"Listing windows:\n{result.stdout}")
            return result.stdout.splitlines()
