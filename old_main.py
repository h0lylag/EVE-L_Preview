import os
import sys
import json
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, QVBoxLayout,
    QCheckBox, QLabel, QWidget, QTabWidget, QLineEdit, QHBoxLayout
)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QThread, QTimer, pyqtSignal
from Xlib.error import BadDrawable

CONFIG_FILE = "EVE-L_Preview.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "metadata": {
            "lastmodified": str(datetime.now())
        },
        "settings": {
            "thumbnail_scaling": 7.5,
            "thumbnail_opacity": 100,
            "application_position": [100, 100],
            "enable_borders": True,
            "active_border_color": "#47f73e",
            "inactive_border_color": "#808080"
        },
        "thumbnail_position": {}
    }

def save_config(config):
    config["metadata"]["lastmodified"] = str(datetime.now())
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

class X11Interface:
    def __init__(self):
        pass

    def capture_window(self, window_id):
        from Xlib import X, display  # Importing here to avoid global import issues
        self.display = display.Display()
        window = self.display.create_resource_object('window', window_id)
        geom = window.get_geometry()
        width, height = geom.width, geom.height

        # Capture window contents into an image
        raw = window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)

        # Convert raw image data to a QImage directly
        image = QImage(raw.data, width, height, QImage.Format_RGB32)

        return image, width, height

    def focus_and_raise_window(self, window_id):
        # Using wmctrl to bring the window to the front
        wmctrl_command = ['wmctrl', '-i', '-a', window_id]
        subprocess.call(wmctrl_command)

    def list_windows(self):
        # Using wmctrl to list all windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        return result.stdout.splitlines()

class UpdateThread(QThread):
    updated = pyqtSignal(QPixmap, int, int)
    error_occurred = pyqtSignal()

    def __init__(self, x11_interface, window_id, window_title, interval=1000):
        super().__init__()
        self.x11_interface = x11_interface
        self.window_id = window_id
        self.window_title = window_title
        self.interval = interval

    def run(self):
        while True:
            try:
                image, original_width, original_height = self.x11_interface.capture_window(int(self.window_id, 16))

                # Scale image to % of the original size
                scale_factor = config["settings"]["thumbnail_scaling"] / 100

                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                image = image.scaled(new_width, new_height, Qt.KeepAspectRatio)
                pixmap = QPixmap.fromImage(image)

                # Draw character name on pixmap
                painter = QPainter(pixmap)
                painter.setPen(QColor('white'))
                painter.setFont(QFont('Roboto Mono', 10))
                if " - " in self.window_title:
                    character_name = self.window_title.split(" - ")[-1]
                else:
                    character_name = "Unknown"
                painter.drawText(10, 20, character_name)
                painter.end()

                self.updated.emit(pixmap, new_width, new_height)
            except BadDrawable:
                self.error_occurred.emit()
                break
            except Exception as e:
                print(f"Error updating preview: {e}")
            self.msleep(self.interval)

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


class WindowManager:
    def __init__(self, x11_interface, config):
        self.x11_interface = x11_interface
        self.config = config
        self.previews = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_previews)
        self.timer.start(1000)
        self.active_preview = None

    def update_previews(self):
        window_list = self.x11_interface.list_windows()
        eve_windows = [(line.split()[0], " ".join(line.split()[3:])) for line in window_list if "EVE - " in line]
        current_ids = {preview.window_id for preview in self.previews}

        new_windows = [(window_id, window_title) for window_id, window_title in eve_windows if window_id not in current_ids]
        closed_windows = [preview for preview in self.previews if preview.window_id not in {window_id for window_id, _ in eve_windows}]

        for window_id, window_title in new_windows:
            preview = WindowPreview(self.x11_interface, window_id, window_title, self.previews, self.config, self)
            preview.show()
            self.previews.append(preview)

        for preview in closed_windows:
            self.previews.remove(preview)
            preview.close()

        for preview in self.previews:
            preview.update_border()

    def set_active_preview(self, preview):
        if self.active_preview:
            self.active_preview.update_border()
        self.active_preview = preview
        self.active_preview.update_border()
        self.update_all_borders()

    def update_all_borders(self):
        for preview in self.previews:
            preview.update_border()


class ThumbnailsTab(QWidget):
    def __init__(self, parent=None):
        super(ThumbnailsTab, self).__init__(parent)
        layout = QVBoxLayout()

        self.enable_borders_checkbox = QCheckBox("Enable Borders")
        self.enable_borders_checkbox.setChecked(config["settings"]["enable_borders"])
        self.enable_borders_checkbox.stateChanged.connect(self.toggle_borders)

        self.active_border_color_label = QLabel("Active Client Border Color:")
        self.active_border_color_input = QLineEdit(config["settings"]["active_border_color"])

        self.inactive_border_color_label = QLabel("Inactive Client Border Color:")
        self.inactive_border_color_input = QLineEdit(config["settings"]["inactive_border_color"])

        layout.addWidget(self.enable_borders_checkbox)
        layout.addWidget(self.active_border_color_label)
        layout.addWidget(self.active_border_color_input)
        layout.addWidget(self.inactive_border_color_label)
        layout.addWidget(self.inactive_border_color_input)

        self.setLayout(layout)

        self.active_border_color_input.editingFinished.connect(self.update_active_border_color)
        self.inactive_border_color_input.editingFinished.connect(self.update_inactive_border_color)

    def toggle_borders(self, state):
        config["settings"]["enable_borders"] = bool(state)
        save_config(config)

    def update_active_border_color(self):
        color = self.active_border_color_input.text()
        if self.is_valid_hex_color(color):
            config["settings"]["active_border_color"] = color
            save_config(config)

    def update_inactive_border_color(self):
        color = self.inactive_border_color_input.text()
        if self.is_valid_hex_color(color):
            config["settings"]["inactive_border_color"] = color
            save_config(config)

    def is_valid_hex_color(self, color):
        if color.startswith('#') and len(color) == 7:
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                pass
        return False

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("EVE-L Preview")
        self.setGeometry(100, 100, 400, 300)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.setToolTip("EVE-L Preview")

        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        self.tray_icon.show()

        self.init_ui()
        self.load_position()

    def init_ui(self):
        self.tabs = QTabWidget()

        self.general_tab = GeneralTab()
        self.settings_tab = SettingsTab()
        self.thumbnails_tab = ThumbnailsTab()
        self.profiles_tab = ProfilesTab()

        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.settings_tab, "Settings")
        self.tabs.addTab(self.thumbnails_tab, "Thumbnails")
        self.tabs.addTab(self.profiles_tab, "Profiles")

        self.setCentralWidget(self.tabs)

    def closeEvent(self, event):
        self.save_position()
        if self.isVisible():
            event.ignore()
            self.hide()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def load_position(self):
        pos = config["settings"].get("application_position", [100, 100])
        self.move(pos[0], pos[1])

    def save_position(self):
        config["settings"]["application_position"] = [self.x(), self.y()]
        save_config(config)

class GeneralTab(QWidget):
    def __init__(self, parent=None):
        super(GeneralTab, self).__init__(parent)
        layout = QVBoxLayout()

        self.checkbox1 = QCheckBox("General option 1")
        self.checkbox2 = QCheckBox("General option 2")

        layout.addWidget(self.checkbox1)
        layout.addWidget(self.checkbox2)

        self.setLayout(layout)

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super(SettingsTab, self).__init__(parent)
        layout = QVBoxLayout()

        self.checkbox1 = QCheckBox("Settings option 1")
        self.checkbox2 = QCheckBox("Settings option 2")

        layout.addWidget(self.checkbox1)
        layout.addWidget(self.checkbox2)

        self.setLayout(layout)

class ProfilesTab(QWidget):
    def __init__(self, parent=None):
        super(ProfilesTab, self).__init__(parent)
        layout = QVBoxLayout()

        self.checkbox1 = QCheckBox("Profiles option 1")
        self.checkbox2 = QCheckBox("Profiles option 2")

        layout.addWidget(self.checkbox1)
        layout.addWidget(self.checkbox2)

        self.setLayout(layout)

def main():
    global config
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Load config
    config = load_config()

    # Create main window
    window = MainWindow()
    window_manager = WindowManager(X11Interface(), config)
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
