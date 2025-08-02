# EVE-L Preview

Vibe-coded "native" Linux implementation of EVE-O Preview

## Features That Definitely Work™

- 📷 Live window thumbnails
- 🖱️ Drag & drop positioning
- ⌨️ Tab/Shift+Tab hotkeys
- 🎨 Window borders
- 💾 Config persistence
- 🔧 NixOS support

## Installation & Usage

### The Traditional Way
```bash
pip install -r requirements.txt
python main.py
```

### The Nix Way (For Cultists)
```bash
nix develop
python main.py
```

## Dependencies

### Python Packages
- `PyQt5` - GUI framework
- `python-xlib` - X11 interface
- `keyboard` - Global hotkey support (requires root)

### System Packages
- `wmctrl` - Window management commands
- `xdotool` - X11 automation utilities  
- `maim` - Screenshot capture for thumbnails
- `xwininfo` - Window geometry info (part of x11-utils)

## Configuration

- The app auto-generates a config in `~/.config/EVE-L_Preview/EVE-L_Preview.json`
- If you run with sudo it will try to access the config of the original user

## Known Issues & Quirks

- This was written with my computer and environment in mind. It was only tested here
- Hotkeys require root privileges (blame Wayland)
- May or may not work on your specific window manager
- Code quality ranges from "okayish" to "what the hell is this"

## Contributing

Found a bug? Have a feature idea? Want to refactor my spaghetti code? PRs welcome! 

## License

MIT - Do whatever you want with this beautiful mess.

---

*Built with ❤️, questionable architectural decisions, and way too much coffee.*