import subprocess, logging, threading, shutil
from pathlib import Path
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QByteArray

# Add PIL support for better image processing
from PIL import Image, ImageOps
import io

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class X11Interface:
    """
    * Grab window with maim → stdout (no temp files)
    * Process with PIL for better quality and borders
    * Scale down immediately to thumbnail size
    * Thread-safe with logging for better diagnostics
    """

    def __init__(self, config):
        self.lock = threading.Lock()
        self.config = config

    # ---------------- capture ------------------------------------------
    def capture_window(self, window_id):
        with self.lock:
            # Convert to int if it's a hex string
            win_id = int(window_id, 16) if isinstance(window_id, str) else window_id
            wid_hex = hex(win_id)
            
            logging.debug(f"Capturing window: {wid_hex}")
            
            try:
                # Capture directly to stdout - no temp files
                jpg_data = subprocess.check_output(
                    ["maim", "-i", wid_hex, "-f", "jpg", "-m", "2", "-o"],
                    stderr=subprocess.DEVNULL
                )
                
                # Create QImage directly from bytes
                qt_img = QImage.fromData(jpg_data, "JPG")
                if qt_img.isNull():
                    logging.error(f"Failed to create valid image from maim output")
                    return None, 0, 0
                
                # Process with PIL for borders and scaling
                buffer = QByteArray(jpg_data)
                pil_img = Image.open(io.BytesIO(jpg_data))
                
                # Add border if enabled
                if self.config["settings"].get("enable_borders", True):
                    border_color = self.config["settings"].get("inactive_border_color", "#808080")
                    border_size = self.config["settings"].get("border_size", 5)
                    pil_img = ImageOps.expand(pil_img, border=border_size, fill=border_color)
                
                # Scale according to config
                scale = self.config["settings"]["thumbnail_scaling"] / 100.0
                w, h = int(pil_img.width * scale), int(pil_img.height * scale)
                pil_img = pil_img.resize((w, h), Image.Resampling.LANCZOS)
                
                # Convert back to QImage for Qt compatibility
                buffer = io.BytesIO()
                pil_img.save(buffer, format="JPEG")
                qt_img = QImage.fromData(QByteArray(buffer.getvalue()), "JPG")
                
                logging.debug(f"Captured {wid_hex} → {w}×{h} thumbnail")
                return qt_img, w, h
                
            except subprocess.CalledProcessError as e:
                logging.error(f"maim process failed: {e}")
                return None, 0, 0
            except Exception as e:
                logging.error(f"Capture failed: {e}")
                return None, 0, 0

    # ---------------- misc helpers -------------------------------------
    @staticmethod
    def focus_and_raise_window(window_id):
        # Convert to hex string if it's an int
        win_id = hex(window_id) if isinstance(window_id, int) else window_id
        try:
            subprocess.call(["wmctrl", "-i", "-a", win_id])
        except Exception as e:
            logging.debug(f"wmctrl focus failed: {e}")

    def list_windows(self):
        with self.lock:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True)
            logging.debug(f"Listing windows:\n{res.stdout}")
            return res.stdout.splitlines()
