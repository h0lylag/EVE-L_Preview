import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.config import load_config
from utils.hotkeys import HotkeyManager  # Import HotkeyManager
from utils.window_manager import WindowManager
from utils.x11_interface import X11Interface

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Set application desktop file to group windows
    app.setDesktopFileName("eve-l-preview")

    config = load_config()
    x11_interface = X11Interface(config)
    window_manager = WindowManager(x11_interface, config)  # Remove None

    main_window = MainWindow(config, window_manager)
    main_window

    hotkey_manager = HotkeyManager(main_window, window_manager)
    window_manager.hotkey_manager = hotkey_manager  # Set hotkey_manager

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
