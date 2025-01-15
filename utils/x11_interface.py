import subprocess
from Xlib import X, display
from PyQt5.QtGui import QImage

class X11Interface:
    def __init__(self):
        pass

    def capture_window(self, window_id):
        from Xlib import X, display  # Import here to avoid global import issues
        self.display = display.Display()
        window = self.display.create_resource_object('window', window_id)
        geom = window.get_geometry()
        width, height = geom.width, geom.height

        # Capture window contents into an image
        raw = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)

        # Convert raw image data to a QImage
        image = QImage(raw.data, width, height, QImage.Format_RGB32)

        return image, width, height  # ✅ Returns QImage (fixes 'bytes' object error)

    def focus_and_raise_window(self, window_id):
        # Using wmctrl to bring the window to the front
        wmctrl_command = ['wmctrl', '-i', '-a', window_id]
        subprocess.call(wmctrl_command)

    def list_windows(self):
        # Using wmctrl to list all windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        return result.stdout.splitlines()
