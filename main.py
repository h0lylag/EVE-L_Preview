import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.config import load_config
from utils.x11_interface import X11Interface
from utils.window_manager import WindowManager

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = load_config()
    x11_interface = X11Interface()
    window_manager = WindowManager(x11_interface, config)  # ✅ Ensure previews work

    main_window = MainWindow(config, window_manager)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
