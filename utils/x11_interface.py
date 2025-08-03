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
    def get_kwin_window_id(self, x11_window_id):
        """Map X11 window ID to KWin UUID by matching PIDs and window names"""
        try:
            # Get X11 window info using wmctrl
            x11_hex = hex(x11_window_id) if isinstance(x11_window_id, int) else x11_window_id
            x11_decimal = int(x11_hex, 16)
            
            # Get window info from wmctrl
            wmctrl_result = subprocess.run(["wmctrl", "-l", "-p"], capture_output=True, text=True)
            if wmctrl_result.returncode != 0:
                return None
                
            x11_pid = None
            x11_name = None
            for line in wmctrl_result.stdout.splitlines():
                parts = line.split(None, 4)
                if len(parts) >= 5:
                    win_id = int(parts[0], 16)
                    if win_id == x11_decimal:
                        x11_pid = parts[2]
                        x11_name = parts[4]
                        break
            
            if not x11_pid:
                logging.debug(f"Could not find X11 window info for {x11_hex}")
                return None
            
            # Search KWin windows and match by PID and name
            kdotool_result = subprocess.run([
                "kdotool", "search", "--pid", x11_pid, "--name", x11_name
            ], capture_output=True, text=True)
            
            if kdotool_result.returncode == 0 and kdotool_result.stdout.strip():
                kwin_uuid = kdotool_result.stdout.strip().split('\n')[0]
                logging.debug(f"Mapped X11 {x11_hex} -> KWin {kwin_uuid}")
                return kwin_uuid
                
        except Exception as e:
            logging.debug(f"Failed to map X11 ID {x11_window_id} to KWin UUID: {e}")
        
        return None

    def focus_and_raise_window(self, window_id):
        # Convert to hex string if it's an int
        win_id = hex(window_id) if isinstance(window_id, int) else window_id
        
        try:
            # Method 1: Try kdotool with KWin UUID mapping
            kwin_uuid = self.get_kwin_window_id(window_id)
            if kwin_uuid:
                result = subprocess.run([
                    "kdotool", "windowactivate", kwin_uuid
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Add mouse jiggle for EVE multiboxing workflow
                    self._trigger_mouse_detection()
                    logging.debug(f"Successfully focused window {win_id} using kdotool")
                    return
                else:
                    logging.debug(f"kdotool activation failed: {result.stderr}")
            
        except Exception as e:
            logging.debug(f"kdotool focus failed: {e}")
        
        try:
            # Method 2: Fallback to wmctrl
            subprocess.call(["wmctrl", "-i", "-a", win_id])
            # Add mouse jiggle for EVE multiboxing workflow
            self._trigger_mouse_detection()
            logging.debug(f"Successfully focused window {win_id} using wmctrl fallback")
                    
        except Exception as e:
            logging.debug(f"Window focus failed: {e}")

    def _trigger_mouse_detection(self):
        """Tiny mouse movement to trigger EVE's mouse detection for multiboxing"""
        logging.debug("Attempting mouse jiggle for EVE multiboxing...")
        try:
            # More visible movement for testing: 5 pixels right, brief pause, then 5 pixels left
            result1 = subprocess.run(["xdotool", "mousemove_relative", "1", "0"], 
                         capture_output=True, text=True, timeout=1)
            
            # Small delay to make movement visible
            import time
            time.sleep(0.05)  # 50ms pause
            
            result2 = subprocess.run(["xdotool", "mousemove_relative", "--", "-1", "0"], 
                         capture_output=True, text=True, timeout=1)
            
            if result1.returncode == 0 and result2.returncode == 0:
                logging.debug("Mouse jiggle completed successfully")
            else:
                logging.debug(f"Mouse jiggle failed: result1={result1.returncode}, result2={result2.returncode}")
                logging.debug(f"stderr1: {result1.stderr}, stderr2: {result2.stderr}")
                
        except subprocess.TimeoutExpired:
            logging.debug("xdotool mouse jiggle timed out")
        except FileNotFoundError:
            logging.debug("xdotool not found, trying KDE shortcut fallback")
            try:
                result = subprocess.run([
                    "qdbus", "org.kde.kglobalaccel", "/component/kwin",
                    "invokeShortcut", "MoveMouseToFocus"
                ], capture_output=True, text=True, timeout=1)
                if result.returncode == 0:
                    logging.debug("KDE MoveMouseToFocus shortcut executed")
                else:
                    logging.debug(f"KDE shortcut failed: {result.stderr}")
            except Exception as kde_e:
                logging.debug(f"KDE shortcut also failed: {kde_e}")
        except Exception as e:
            logging.debug(f"Mouse detection trigger failed: {e}")
            pass

    def list_windows(self):
        """List windows using wmctrl (kdotool search doesn't provide same format)"""
        try:
            res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True)
            logging.debug(f"Listed {len(res.stdout.splitlines())} windows using wmctrl")
            return res.stdout.splitlines()
        except Exception as e:
            logging.error(f"wmctrl window listing failed: {e}")
            return []
