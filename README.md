# EVE-L Preview

Vibe-coded Linux implementation of EVE-O Preview

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