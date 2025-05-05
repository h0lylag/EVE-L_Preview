from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor

class BorderWindow(QWidget):
    """A separate transparent window that only shows a colored border"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
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
        self.raise_()
    
    def update_position(self):
        """Update position and size to match target window"""
        if not self.target_window:
            return
            
        # Position border window to surround target window with slight padding
        geom = self.target_window.frameGeometry()
        self.setGeometry(
            geom.x() - self.border_width,
            geom.y() - self.border_width,
            geom.width() + (self.border_width * 2),
            geom.height() + (self.border_width * 2)
        )
    
    def paintEvent(self, event):
        """Draw just the border"""
        painter = QPainter(self)
        painter.setPen(QColor(self.border_color))
        painter.setRenderHint(QPainter.Antialiasing)
        
        for i in range(self.border_width):
            painter.drawRect(i, i, self.width() - i*2 - 1, self.height() - i*2 - 1)