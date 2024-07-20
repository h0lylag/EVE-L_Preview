import os
import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont
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

        # Convert raw image data to a QImage directly
        image = QImage(raw.data, width, height, QImage.Format_RGB32)

        return image, width, height

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

    def __init__(self, x11_interface, window_id, window_title, interval=1000):
        super().__init__()
        self.x11_interface = x11_interface
        self.window_id = window_id
        self.window_title = window_title
        self.interval = interval

    def run(self):
        while True:
            try:
                image, original_width, original_height = self.x11_interface.capture_window(int(self.window_id, 16))

                # Scale image to % of the original size
                scale_factor = 0.085

                # something going on were the right side of the preview gets cut off.
                # this is a terrible hacky workaround that adds 100 pixels to the width but then we use KeepAspectRatio
                # No idea why this works, but it does
                new_width = int(original_width * scale_factor) + 100
                new_height = int(original_height * scale_factor)
                image = image.scaled(new_width, new_height, Qt.KeepAspectRatio)
                pixmap = QPixmap.fromImage(image)

                # Draw character name on pixmap
                painter = QPainter(pixmap)
                painter.setPen(QColor('white'))
                painter.setFont(QFont('Arial', 10))
                if " - " in self.window_title:
                    character_name = self.window_title.split(" - ")[-1]
                else:
                    character_name = "Unknown"
                painter.drawText(10, 20, character_name)
                painter.end()

                self.updated.emit(pixmap, new_width, new_height)
            except Exception as e:
                print(f"Error updating preview: {e}")
            self.msleep(self.interval)

class WindowPreview(QWidget):
    def __init__(self, x11_interface, window_id, window_title, previews):
        super().__init__()
        self.window_id = window_id
        self.window_title = window_title
        self.x11_interface = x11_interface
        self.previews = previews
        self.label = QLabel(self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.capture_interval = 1000  # Capture every 1000 ms (1 second)

        self.dragging = False
        self.drag_position = QPoint()

        self.update_thread = UpdateThread(x11_interface, window_id, window_title, self.capture_interval)
        self.update_thread.updated.connect(self.set_pixmap)
        self.update_thread.start()

    def set_pixmap(self, pixmap, new_width, new_height):
        self.label.setPixmap(pixmap)
        self.setFixedSize(new_width, new_height + 20)  # Add extra height to accommodate the text
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
            #print(f"Moving to: {new_position}")
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
    eve_windows = [(line.split()[0], " ".join(line.split()[3:])) for line in window_list if "EVE - " in line]

    # Create a preview window for each EVE window
    preview_windows = []
    for window_id, window_title in eve_windows:
        preview_window = WindowPreview(x11_interface, window_id, window_title, preview_windows)
        preview_window.show()
        preview_windows.append(preview_window)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
