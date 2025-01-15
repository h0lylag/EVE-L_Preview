from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from utils.update_thread import UpdateThread
from utils.config import save_config

class WindowPreview(QWidget):
    SNAP_DISTANCE = 20

    def __init__(self, x11_interface, window_id, window_title, previews, config, manager):
        super().__init__()
        self.window_id = window_id
        self.window_title = window_title
        self.x11_interface = x11_interface
        self.previews = previews
        self.config = config
        self.manager = manager
        self.label = QLabel(self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove any layout margins
        self.setLayout(layout)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setContentsMargins(0, 0, 0, 0)  # Remove widget margins
        self.setWindowOpacity(config["settings"]["thumbnail_opacity"] / 100)
        self.capture_interval = 1000  # Capture every 1000 ms (1 second)

        self.dragging = False
        self.drag_position = QPoint()

        self.update_thread = UpdateThread(x11_interface, window_id, window_title, self.capture_interval)
        self.update_thread.updated.connect(self.set_pixmap)
        self.update_thread.error_occurred.connect(self.handle_error)
        self.update_thread.start()

        self.load_position()
        self.update_border()

    def set_pixmap(self, pixmap, new_width, new_height):
        self.label.setPixmap(pixmap)
        self.setFixedSize(new_width, new_height)
        self.adjustSize()

    def handle_error(self):
        self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.x11_interface.focus_and_raise_window(self.window_id)
            self.manager.set_active_preview(self)
        elif event.button() == Qt.RightButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            print(f"Started dragging: {self.drag_position}")
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.RightButton:
            new_position = event.globalPos() - self.drag_position
            self.move(new_position)
            self.snap_to_grid()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.dragging = False
            print("Stopped dragging")
            self.save_position()
            event.accept()

    def snap_to_grid(self):
        for preview in self.previews:
            if preview == self:
                continue

            r1 = self.frameGeometry()
            r2 = preview.frameGeometry()

            # Check for horizontal snapping
            if abs(r1.right() - r2.left()) < self.SNAP_DISTANCE:
                self.move(r2.left() - r1.width(), self.y())
            elif abs(r1.left() - r2.right()) < self.SNAP_DISTANCE:
                self.move(r2.right(), self.y())
            elif abs(r1.left() - r2.left()) < self.SNAP_DISTANCE:
                self.move(r2.left(), self.y())
            elif abs(r1.right() - r2.right()) < self.SNAP_DISTANCE:
                self.move(r2.right() - r1.width(), self.y())

            # Check for vertical snapping
            if abs(r1.bottom() - r2.top()) < self.SNAP_DISTANCE:
                self.move(self.x(), r2.top() - r1.height())
            elif abs(r1.top() - r2.bottom()) < self.SNAP_DISTANCE:
                self.move(self.x(), r2.bottom())
            elif abs(r1.top() - r2.top()) < self.SNAP_DISTANCE:
                self.move(self.x(), r2.top())
            elif abs(r1.bottom() - r2.bottom()) < self.SNAP_DISTANCE:
                self.move(self.x(), r2.bottom() - r1.height())

    def load_position(self):
        character_name = self.get_character_name()
        if character_name in self.config["thumbnail_position"]:
            pos = self.config["thumbnail_position"][character_name]
            self.move(pos[0], pos[1])

    def save_position(self):
        character_name = self.get_character_name()
        self.config["thumbnail_position"][character_name] = [self.x(), self.y()]
        save_config(self.config)

    def get_character_name(self):
        if " - " in self.window_title:
            return self.window_title.split(" - ")[-1]
        return "Unknown"

    def update_border(self):
        if self.config["settings"]["enable_borders"]:
            border_color = self.config["settings"]["inactive_border_color"]
            if self.manager.active_preview == self:
                border_color = self.config["settings"]["active_border_color"]
            self.setStyleSheet(f"QWidget {{ border: 3px solid {border_color}; }}")
        else:
            self.setStyleSheet("QWidget { border: none; }")
