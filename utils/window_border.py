from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor

class BorderWindow(QWidget):
    """A transparent window that draws an inside border on top of the preview"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        
        # Add more flags to completely hide from taskbar and window switching
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |                 # Not shown in taskbar
            Qt.X11BypassWindowManagerHint  # Specifically for X11/Linux
        )
        
        # Add these three crucial attributes
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        # Remove Qt.WA_TransparentForMouseEvents to handle mouse events ourselves
        self.setFocusPolicy(Qt.NoFocus)
        
        self.target_window = None
        self.border_color = config["settings"].get("active_border_color", "#47f73e")
        self.border_width = 3
        self.hide()
    
    def follow(self, window):
        """Set the window to follow and show border"""
        if window is None:
            self.hide()
            return
            
        self.target_window = window
        self.update_position()
        self.show()
        self.raise_()  # Keep border on top of the preview
    
    def update_position(self):
        """Update position and size to exactly match target window"""
        if not self.target_window:
            return
            
        # Position border window to exactly overlap the target window
        geom = self.target_window.frameGeometry()
        self.setGeometry(
            geom.x(),
            geom.y(),
            geom.width(),
            geom.height()
        )
    
    def paintEvent(self, event):
        """Draw just the border inside the widget boundary"""
        painter = QPainter(self)
        painter.setPen(QColor(self.border_color))
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw multiple lines inward from the edge
        for i in range(self.border_width):
            painter.drawRect(i, i, self.width() - i*2 - 1, self.height() - i*2 - 1)

    def mousePressEvent(self, event):
        """Start dragging when right-clicking on border"""
        if event.button() == Qt.RightButton and self.target_window:
            # Start dragging on the target window
            self.target_window.dragging = True
            self.target_window.drag_position = event.globalPos() - self.target_window.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.LeftButton and self.target_window:
            # Handle left-click to focus window
            self.target_window.x11_interface.focus_and_raise_window(self.target_window.window_id)
            if self.target_window.manager.get_last_active_client() != self.target_window.window_id:
                self.target_window.manager.set_last_active_client(self.target_window.window_id)
                self.target_window.manager.hotkey_manager.update_current_index(self.target_window.window_id)

    def mouseMoveEvent(self, event):
        """Handle dragging movement"""
        if self.target_window and self.target_window.dragging and event.buttons() & Qt.RightButton:
            new_position = event.globalPos() - self.target_window.drag_position
            self.target_window.move(new_position)
            # Update border position to follow the window
            self.update_position()
            event.accept()

    def mouseReleaseEvent(self, event):
        """Stop dragging and snap"""
        if event.button() == Qt.RightButton and self.target_window and self.target_window.dragging:
            self.target_window.dragging = False
            # Snap to grid and save position
            self.target_window.snap_to_grid()
            self.update_position()  # Update border after snapping
            self.target_window.save_position()
            event.accept()