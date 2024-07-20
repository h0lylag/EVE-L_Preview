import os
import sys
import subprocess
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer, Qt, QPoint, QThread, pyqtSignal

class X11Interface:
    def __init__(self):
        pass

    def capture_window(self, window_id):
        from Xlib import X, display  # Importing here to avoid global import issues
        self.display = display.Display()
        window = self.display.create_resource_object('window', window_id)
        geom = window.get_geometry()
        width, height = geom.width, geom.height

        # Capture window contents into an image
        raw = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)

        # Convert raw image to numpy array
        raw_image = np.frombuffer(raw.data, dtype=np.uint8).reshape((height, width, 4))

        return raw_image, width, height

    def focus_and_raise_window(self, window_id):
        # Using wmctrl to bring the window to the front
        wmctrl_command = ['wmctrl', '-i', '-a', window_id]
        subprocess.call(wmctrl_command)

    def list_windows(self):
        # Using wmctrl to list all windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        return result.stdout.splitlines()

class UpdateThread(QThread):
    updated = pyqtSignal(QPixmap, int, int)

    def __init__(self, x11_interface, window_id, interval=1000):
        super().__init__()
        self.x11_interface = x11_interface
        self.window_id = window_id
        self.interval = interval

    def run(self):
        while True:
            try:
                raw_image, original_width, original_height = self.x11_interface.capture_window(int(self.window_id, 16))
                image = QImage(raw_image.data, original_width, original_height, QImage.Format_RGB32)

                # Scale image to 10% of the original size
                new_width = int(original_width * 0.085)
                new_height = int(original_height * 0.085)
                image = image.scaled(new_width, new_height, Qt.KeepAspectRatio)
                pixmap = QPixmap.fromImage(image)
                self.updated.emit(pixmap, new_width, new_height)
            except Exception as e:
                print(f"Error updating preview: {e}")
            self.msleep(self.interval)

class WindowPreview(QWidget):
    def __init__(self, x11_interface, window_id, previews):
        super().__init__()
        self.window_id = window_id
        self.x11_interface = x11_interface
        self.previews = previews
        self.label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.capture_interval = 500  # Capture every 1000 ms (1 second)

        self.dragging = False
        self.drag_position = QPoint()

        self.update_thread = UpdateThread(x11_interface, window_id, self.capture_interval)
        self.update_thread.updated.connect(self.set_pixmap)
        self.update_thread.start()

    def set_pixmap(self, pixmap, new_width, new_height):
        self.label.setPixmap(pixmap)
        self.setFixedSize(new_width, new_height)
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.x11_interface.focus_and_raise_window(self.window_id)
        elif event.button() == Qt.RightButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            print(f"Started dragging: {self.drag_position}")
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.RightButton:
            new_position = event.globalPos() - self.drag_position
            self.move(new_position)
            print(f"Moving to: {new_position}")
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.dragging = False
            print("Stopped dragging")
            event.accept()

def main():
    app = QApplication(sys.argv)
    x11_interface = X11Interface()

    # List all windows and filter those with "EVE - " in the title
    window_list = x11_interface.list_windows()
    eve_windows = [line.split()[0] for line in window_list if "EVE - " in line]

    # Create a preview window for each EVE window
    preview_windows = []
    for window_id in eve_windows:
        preview_window = WindowPreview(x11_interface, window_id, preview_windows)
        preview_window.show()
        preview_windows.append(preview_window)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
