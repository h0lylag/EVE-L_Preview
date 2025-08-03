from PyQt5.QtWidgets import QMainWindow, QSystemTrayIcon, QAction, QMenu, QTabWidget, QApplication
from PyQt5.QtGui import QIcon
from .thumbnails_tab import ThumbnailsTab
from .general_tab import GeneralTab
from .settings_tab import SettingsTab
from .profiles_tab import ProfilesTab
from .hotkeys_tab import HotkeysTab  # Import HotkeysTab
from utils.config import load_config, save_config

class MainWindow(QMainWindow):
    def __init__(self, config, window_manager, x11_interface):
        super().__init__()
        self.config = config  
        self.x11_interface = x11_interface  # Store X11Interface for hotkey access
        self.setWindowTitle("EVE-L Preview")
        self.setGeometry(100, 100, 600, 450)

        self.tray_icon = QSystemTrayIcon(QIcon("assets/icon.png"), self)
        self.tray_icon.setToolTip("EVE-L Preview")
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(lambda: self.close())
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tabs = QTabWidget()
        self.tabs.addTab(ThumbnailsTab(self.config), "Thumbnails")  
        self.tabs.addTab(SettingsTab(self.config), "Settings")      
        self.tabs.addTab(ProfilesTab(self.config), "Profiles")      
        self.tabs.addTab(GeneralTab(self.config), "General")        
        self.tabs.addTab(HotkeysTab(self.config), "Hotkeys")  # Add Hotkeys tab
        self.setCentralWidget(self.tabs)

    def closeEvent(self, event):
        # This is called when self.close() is executed
        if event.spontaneous():
            # If user clicks X button, just hide and keep running
            event.ignore()
            self.hide()
        else:
            # If programmatically closed (i.e., Exit from tray)
            QApplication.quit()
