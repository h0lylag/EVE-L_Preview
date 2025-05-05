#!/usr/bin/env python3
"""
EVE‑L Preview – wlroots screencopy edition
  • Primary capture path: grim + swaymsg / hyprctl  (wlr‑screencopy)
  • Fallback: QScreen.grabWindow (works on X11 / Xwayland)
  • Defaults thumbnail_scaling to 75 %
  • Adds choose_mono_font() and forces QT_QPA_PLATFORM=xcb if Wayland plugin missing
"""

import os, sys, json, subprocess, shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout,
    QLabel, QWidget
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QColor, QFont, QFontDatabase
)
from PyQt5.QtCore import Qt, QPoint, QThread, QTimer, pyqtSignal

CONFIG_FILE = "EVE-L_Preview.json"
CAPTURE_INTERVAL = 500  # milliseconds


# ───────── Config helpers ────────────────────────────────────────────────
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "metadata": {"lastmodified": str(datetime.now())},
        "settings": {
            "thumbnail_scaling": 75,
            "thumbnail_opacity": 100,
            "application_position": [100, 100],
            "enable_borders": True,
            "active_border_color": "#47f73e",
            "inactive_border_color": "#808080",
        },
        "thumbnail_position": {},
    }


def save_config(cfg):
    cfg["metadata"]["lastmodified"] = str(datetime.now())
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)


# ───────── Font helper ───────────────────────────────────────────────────
def choose_mono_font(pt=10) -> QFont:
    fam = "Roboto Mono"
    if fam not in QFontDatabase().families():
        fam = QFontDatabase.systemFont(QFontDatabase.FixedFont).family()
    return QFont(fam, pt)


# ───────── Screen‑capture helper: maim, JPG 80 % ─────────────────────────
def _maim_capture_window(win_id: int) -> QImage | None:
    """
    Grab the contents of an X11 / XWayland window using **maim** and return it
    as a QImage.  ‑‑  Requires maim ≥ 5.5 built with imlib2‑jpg support.

        win_id  – integer X window id (same value wmctrl prints)

    maim flags used:
      • -i <id>         capture that specific window (no decorations)
      • -f jpg          encode as JPEG
      • -m 2            2 quality
      • -o              write to stdout
    """
    if not shutil.which("maim"):
        return None            # maim not installed → let caller handle
    try:
        jpg = subprocess.check_output(
            ["maim", "-i", hex(win_id), "-f", "jpg", "-m", "2", "-o"],
            stderr=subprocess.DEVNULL
        )
        img = QImage.fromData(jpg, "JPG")
        return img if not img.isNull() else None
    except subprocess.CalledProcessError:
        return None


# ───────── Window interface – maim only ─────────────────────────────────
class WindowInterface:
    """
    Simplified interface that **only** uses maim.  Works on:
      • Native X11 sessions
      • Wayland compositors that expose XWayland windows
        (KWin/Plasma, GNOME, Hyprland, Sway‑with‑xwayland etc.)
    """

    # ---- single frame ---------------------------------------------------
    def capture_window(self, win_id: int, _win_title: str):
        img = _maim_capture_window(win_id)
        if img is None:
            raise RuntimeError("maim failed or is unavailable")
        return img, img.width(), img.height()

    # ---- focus / raise (unchanged) -------------------------------------
    @staticmethod
    def focus_and_raise_window(win_id: int):
        subprocess.call(["wmctrl", "-i", "-a", hex(win_id)])

    # ---- list windows (unchanged) --------------------------------------
    @staticmethod
    def list_windows():
        res = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True)
        return res.stdout.splitlines()



# ───────── Background capture thread ────────────────────────────────────
class UpdateThread(QThread):
    updated = pyqtSignal(QPixmap, int, int)
    error_occurred = pyqtSignal()

    def __init__(self, iface: WindowInterface, win_id_hex: str, win_title: str, interval=CAPTURE_INTERVAL):
        super().__init__()
        self.iface, self.win_title = iface, win_title
        self.win_id = int(win_id_hex, 16)
        self.interval = interval

    def run(self):
        while True:
            try:
                img, ow, oh = self.iface.capture_window(self.win_id, self.win_title)
                if img.isNull():
                    raise RuntimeError("null image")

                scale = config["settings"]["thumbnail_scaling"] / 100.0
                nw, nh = int(ow * scale), int(oh * scale)
                img = img.scaled(nw, nh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pix = QPixmap.fromImage(img)

                painter = QPainter(pix)
                painter.setPen(QColor("white"))
                painter.setFont(choose_mono_font(10))
                char = self.win_title.split(" - ")[-1] if " - " in self.win_title else "Unknown"
                painter.drawText(10, 20, char)
                painter.end()

                self.updated.emit(pix, nw, nh)
            except Exception as e:
                print(f"[UpdateThread] capture failed: {e}")
                self.error_occurred.emit()
                break
            self.msleep(self.interval)


# ───────── Preview widget ───────────────────────────────────────────────
class WindowPreview(QWidget):
    SNAP = 20

    def __init__(self, iface, win_id_hex, win_title, previews, cfg, mgr):
        super().__init__()
        self.iface, self.win_id_hex, self.win_title = iface, win_id_hex, win_title
        self.previews, self.cfg, self.mgr = previews, cfg, mgr

        self.label = QLabel(self)
        lay = QVBoxLayout(self)
        lay.addWidget(self.label)
        lay.setContentsMargins(0, 0, 0, 0)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(cfg["settings"]["thumbnail_opacity"] / 100)

        self.dragging = False
        self.drag_pos = QPoint()

        self.thread = UpdateThread(iface, win_id_hex, win_title)
        self.thread.updated.connect(self.set_pixmap)
        self.thread.error_occurred.connect(self.close)
        self.thread.start()

        self.load_pos()
        self.update_border()

    # ---- helpers ----
    def set_pixmap(self, pm, w, h):
        self.label.setPixmap(pm)
        self.setFixedSize(w, h)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.iface.focus_and_raise_window(int(self.win_id_hex, 16))
            self.mgr.set_active(self)
        elif e.button() == Qt.RightButton:
            self.dragging, self.drag_pos = True, e.globalPos() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self.dragging and e.buttons() & Qt.RightButton:
            self.move(e.globalPos() - self.drag_pos)
            self.snap()
            e.accept()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.dragging = False
            self.save_pos()
            e.accept()

    # snapping against other previews
    def snap(self):
        r1 = self.frameGeometry()
        for p in self.previews:
            if p is self:
                continue
            r2 = p.frameGeometry()
            # horizontal
            if abs(r1.right() - r2.left()) < self.SNAP:
                self.move(r2.left() - r1.width(), self.y())
            elif abs(r1.left() - r2.right()) < self.SNAP:
                self.move(r2.right(), self.y())
            elif abs(r1.left() - r2.left()) < self.SNAP:
                self.move(r2.left(), self.y())
            elif abs(r1.right() - r2.right()) < self.SNAP:
                self.move(r2.right() - r1.width(), self.y())
            # vertical
            if abs(r1.bottom() - r2.top()) < self.SNAP:
                self.move(self.x(), r2.top() - r1.height())
            elif abs(r1.top() - r2.bottom()) < self.SNAP:
                self.move(self.x(), r2.bottom())
            elif abs(r1.top() - r2.top()) < self.SNAP:
                self.move(self.x(), r2.top())
            elif abs(r1.bottom() - r2.bottom()) < self.SNAP:
                self.move(self.x(), r2.bottom() - r1.height())

    # position persistence
    def load_pos(self):
        name = self.char_name()
        if name in self.cfg["thumbnail_position"]:
            x, y = self.cfg["thumbnail_position"][name]
            self.move(x, y)

    def save_pos(self):
        name = self.char_name()
        self.cfg["thumbnail_position"][name] = [self.x(), self.y()]
        save_config(self.cfg)

    def char_name(self):
        return self.win_title.split(" - ")[-1] if " - " in self.win_title else "Unknown"

    def update_border(self):
        if self.cfg["settings"]["enable_borders"]:
            col = self.cfg["settings"]["active_border_color"] if self.mgr.active is self \
                  else self.cfg["settings"]["inactive_border_color"]
            self.setStyleSheet(f"QWidget {{ border: 3px solid {col}; }}")
        else:
            self.setStyleSheet("QWidget { border: none; }")


# ───────── Window manager ───────────────────────────────────────────────
class WindowManager:
    def __init__(self, iface, cfg):
        self.iface, self.cfg = iface, cfg
        self.previews = []
        self.active = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def refresh(self):
        lines = self.iface.list_windows()
        eve = [(l.split()[0], " ".join(l.split()[3:])) for l in lines if "EVE - " in l]

        open_ids = {p.win_id_hex for p in self.previews}
        for wid, title in eve:
            if wid not in open_ids:
                pv = WindowPreview(self.iface, wid, title, self.previews, self.cfg, self)
                pv.show()
                self.previews.append(pv)

        valid = {wid for wid, _ in eve}
        for pv in self.previews[:]:
            if pv.win_id_hex not in valid:
                self.previews.remove(pv)
                pv.close()

        self.update_borders()

    def set_active(self, pv):
        if self.active:
            self.active.update_border()
        self.active = pv
        self.update_borders()

    def update_borders(self):
        for p in self.previews:
            p.update_border()


# ───────── main ─────────────────────────────────────────────────────────
def main():
    global config
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = load_config()

    win_iface = WindowInterface()
    win_mgr   = WindowManager(win_iface, config)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
