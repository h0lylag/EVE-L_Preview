from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
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
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Make it click-through
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
        """Pass right-click drag events to target window"""
        if event.button() == Qt.RightButton and self.target_window:
            # Store drag start position
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Move both border and target window together, with perfect synchronization"""
        if self.dragging and event.buttons() & Qt.RightButton and self.target_window:
            new_position = event.globalPos() - self.drag_position
            
            # Move the target window first
            self.target_window.move(new_position)
            
            # Let it snap to grid
            self.target_window.snap_to_grid()
            
            # Update border position to match the potentially snapped position
            self.update_position()
            
            event.accept()

    def mouseReleaseEvent(self, event):
        """End dragging and save position"""
        if event.button() == Qt.RightButton and self.target_window:
            self.dragging = False
            # Save position in target window
            self.target_window.save_position()
            event.accept()