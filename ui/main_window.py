from PyQt5.QtWidgets import QMainWindow, QSystemTrayIcon, QAction, QMenu, QTabWidget
from PyQt5.QtGui import QIcon
from .thumbnails_tab import ThumbnailsTab
from .general_tab import GeneralTab
from .settings_tab import SettingsTab
from .profiles_tab import ProfilesTab
from utils.config import load_config, save_config

class MainWindow(QMainWindow):
    def __init__(self, config, window_manager):
        super().__init__()
        self.config = config  # ✅ Store config
        self.setWindowTitle("EVE-L Preview")
        self.setGeometry(100, 100, 400, 300)

        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self)
        self.tray_icon.setToolTip("EVE-L Preview")
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tabs = QTabWidget()
        self.tabs.addTab(ThumbnailsTab(self.config), "Thumbnails")  # ✅ Pass config properly
        self.tabs.addTab(SettingsTab(self.config), "Settings")      # ✅ Pass config properly
        self.tabs.addTab(ProfilesTab(self.config), "Profiles")      # ✅ Pass config properly
        self.tabs.addTab(GeneralTab(self.config), "General")        # ✅ Pass config properly
        self.setCentralWidget(self.tabs)
