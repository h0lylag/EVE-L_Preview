from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap
from utils.update_thread import UpdateThread
from utils.config import save_config
import logging

class WindowPreview(QWidget):
    SNAP_DISTANCE = 20  # Keep snapping enabled

    def __init__(self, x11_interface, window_id, window_title, previews, config, manager, hotkey_manager):
        super().__init__()
        self.window_id = window_id
        self.window_title = window_title
        self.hotkey_manager = hotkey_manager  # Add hotkey_manager
        self.x11_interface = x11_interface
        self.previews = previews
        self.config = config
        self.manager = manager
        self.label = QLabel(self)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint |
            Qt.Tool  | 
            Qt.X11BypassWindowManagerHint  # Add this to completely hide from taskbar on Linux
        )
        
        # Add this attribute to prevent window from appearing in Alt+Tab
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowOpacity(config["settings"]["thumbnail_opacity"] / 100)
        self.capture_interval = 3000  

        self.dragging = False
        self.drag_position = QPoint()

        self.update_thread = UpdateThread(x11_interface, window_id, window_title, self.capture_interval)
        self.update_thread.updated.connect(self.set_pixmap)
        self.update_thread.error_occurred.connect(self.handle_error)
        self.update_thread.start()

        self.load_position()  # Restore position loading

    def set_pixmap(self, pixmap, new_width, new_height):
        """Update screenshot - no border management needed"""
        self.label.setPixmap(pixmap)
        self.setFixedSize(new_width, new_height)
        self.adjustSize()
        
        # If this window is active, update border position
        if self.manager.get_last_active_client() == self.window_id:
            self.manager.active_border.update_position()

    def handle_error(self):
        self.close()

    def load_position(self):
        """Load the last known position of this preview from the config."""
        character_name = self.get_character_name()
        if character_name in self.config["thumbnail_position"]:
            pos = self.config["thumbnail_position"][character_name]
            logging.debug(f"Loading position for {character_name}: {pos}")
            self.move(pos[0], pos[1])

    def save_position(self):
        """Save the current position of this preview to the config."""
        character_name = self.get_character_name()
        self.config["thumbnail_position"][character_name] = [self.x(), self.y()]
        save_config(self.config)
        logging.debug(f"Saved position for {character_name}: {self.x()}, {self.y()}")

    def get_character_name(self):
        """Extract character name from window title."""
        if " - " in self.window_title:
            return self.window_title.split(" - ")[-1]
        return "Unknown"

    def mousePressEvent(self, event):
        """Detect left or right-click interactions."""
        if event.button() == Qt.LeftButton:
            logging.debug(f"Left-click on {self.window_id} - bringing to front.")
            # Always bring the clicked window to the front
            self.x11_interface.focus_and_raise_window(self.window_id)
            if self.manager.get_last_active_client() != self.window_id:
                self.manager.set_last_active_client(self.window_id)  # Track clicked clients
                self.manager.hotkey_manager.update_current_index(self.window_id)  # Update current index
            else:
                logging.debug(f"Window {self.window_id} is already the active window.")
        elif event.button() == Qt.RightButton:
            logging.debug(f"Right-click on {self.window_id} - start dragging.")
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle dragging movement."""
        if self.dragging and event.buttons() & Qt.RightButton:
            logging.debug(f"Dragging window {self.window_id}")
            new_position = event.globalPos() - self.drag_position
            self.move(new_position)
            self.snap_to_grid()
            event.accept()

    def mouseReleaseEvent(self, event):
        """Stop dragging and save new position."""
        if event.button() == Qt.RightButton:
            logging.debug(f"Released drag on {self.window_id} - saving position.")
            self.dragging = False
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

        logging.debug(f"🔵 Snapped window {self.window_id} into position.")
