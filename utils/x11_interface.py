import subprocess, logging, threading, shutil
from pathlib import Path
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QByteArray

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
        self.config = config

    # ---------------- capture ------------------------------------------
    def capture_window(self, window_id):
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
            
            # Scale directly with Qt instead of using PIL
            scale = self.config["settings"]["thumbnail_scaling"] / 100.0
            w, h = int(qt_img.width() * scale), int(qt_img.height() * scale)
            scaled_img = qt_img.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            logging.debug(f"Captured {wid_hex} → {w}×{h} thumbnail")
            return scaled_img, w, h
            
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
        decimal_id = int(win_id, 16)
        
        try:
            # Method 1: Try KDE qdbus first (most direct)
            result = subprocess.run([
                "qdbus", "org.kde.KWin", "/KWin", 
                "org.kde.KWin.activateWindow", str(decimal_id)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # KDE activation successful, now move mouse to trigger events
                subprocess.call([
                    "qdbus", "org.kde.kglobalaccel", "/component/kwin",
                    "invokeShortcut", "MoveMouseToFocus"
                ])
                logging.debug(f"Successfully focused window {win_id} using KDE qdbus")
                return
            
        except Exception as e:
            logging.debug(f"KDE qdbus focus failed: {e}")
        
        try:
            # Method 2: Fallback to wmctrl only (no xdotool dependency)
            subprocess.call(["wmctrl", "-i", "-a", win_id])
            logging.debug(f"Successfully focused window {win_id} using wmctrl fallback")
                    
        except Exception as e:
            logging.debug(f"Window focus failed: {e}")

    def list_windows(self):
        """List windows using wmctrl (KDE doesn't expose window listing via D-Bus)"""
        try:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True)
            logging.debug(f"Listed {len(res.stdout.splitlines())} windows using wmctrl")
            return res.stdout.splitlines()
        except Exception as e:
            logging.error(f"wmctrl window listing failed: {e}")
            return []
