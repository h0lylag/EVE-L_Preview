import os
import sys
import time
import threading
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage, QMouseEvent
from PyQt5.QtCore import QTimer, Qt, QPoint
from Xlib import X, display

class X11Interface:
    def __init__(self):
        self.display = display.Display()
        self.root = self.display.screen().root

    def capture_window(self, window_id):
        window = self.display.create_resource_object('window', window_id)
        geom = window.get_geometry()
        width, height = geom.width, geom.height

        # Capture window contents into an image
        raw = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)

        # Convert raw image to numpy array
        raw_image = np.frombuffer(raw.data, dtype=np.uint8).reshape((height, width, 4))

        return raw_image, width, height

class WindowPreview(QWidget):
    def __init__(self, x11_interface, window_id):
        super().__init__()
        self.window_id = window_id
        self.x11_interface = x11_interface
        self.label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 236)
        self.capture_interval = 250  # Capture every 250 ms

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_preview)
        self.timer.start(self.capture_interval)

        self.dragging = False
        self.drag_position = QPoint()

    def update_preview(self):
        try:
            raw_image, width, height = self.x11_interface.capture_window(int(self.window_id, 16))
            # Convert raw image to QImage
            image = QImage(raw_image.data, width, height, QImage.Format_RGB32)
            image = image.scaled(420, 236)
            pixmap = QPixmap.fromImage(image)
            self.label.setPixmap(pixmap)
        except Exception as e:
            print(f"Error updating preview: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.RightButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.dragging = False
            event.accept()

def main():
    app = QApplication(sys.argv)
    x11_interface = X11Interface()

    window_id = "0x6600001"  # Change to your target window ID
    preview_window = WindowPreview(x11_interface, window_id)
    preview_window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
