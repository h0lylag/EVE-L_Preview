import logging
import threading
import subprocess
import keyboard  # Replace evdev with keyboard

# Enable logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class HotkeyManager:
    def __init__(self, main_window, window_manager):
        self.main_window = main_window
        self.window_manager = window_manager
        self.current_index = -1  # Track last active character
        self.shift_pressed = False
        self.tab_pressed = False
        
        logging.info("Initializing HotkeyManager with keyboard library...")
        
        # Setup keyboard hooks
        keyboard.on_press_key('shift', self.on_shift_press)
        keyboard.on_release_key('shift', self.on_shift_release)
        keyboard.on_press_key('tab', self.on_tab_press)
        keyboard.on_release_key('tab', self.on_tab_release)
        
        logging.info("Keyboard hooks registered for Tab and Shift+Tab.")

    def on_shift_press(self, e):
        """Track shift key press state"""
        self.shift_pressed = True
        
    def on_shift_release(self, e):
        """Track shift key release state"""
        self.shift_pressed = False
        
    def on_tab_press(self, e):
        """Handle tab key press - only process once per press"""
        if not self.tab_pressed and self.is_eve_window_active():
            self.tab_pressed = True
            logging.debug("Tab key detected!")
            
            if self.shift_pressed:
                logging.debug("Shift + Tab detected - cycling backward")
                self.cycle_characters(reverse=True)
            else:
                logging.debug("Tab key pressed - cycling forward")
                self.cycle_characters(reverse=False)
    
    def on_tab_release(self, e):
        """Reset tab pressed state on release"""
        self.tab_pressed = False

    def is_eve_window_active(self):
        """Check if an EVE window is currently active and in focus."""
        try:
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], 
                                     capture_output=True, text=True)
            active_window_name = result.stdout.strip()
            logging.debug(f"Active window name: {active_window_name}")
            return "EVE - " in active_window_name
        except Exception as e:
            logging.error(f"Error checking active window: {e}")
            return False

    def cycle_characters(self, reverse=False):
        """Cycle through the list of characters, respecting the order in config."""
        logging.debug("Cycling characters...")

        # Get character names from config in user-defined order
        character_list = list(self.main_window.config["hotkeys"]["character_list"].keys())
        logging.debug(f"Character list from config: {character_list}")

        # Get all open EVE windows
        open_windows = self.list_windows()
        eve_windows = [line for line in open_windows if "EVE - " in line]
        logging.debug(f"Open EVE Windows: {eve_windows}")

        # Create a dictionary of window_title -> window_id for easier lookup
        window_dict = {}
        for window in eve_windows:
            parts = window.split(None, 3)
            if len(parts) < 4:
                continue
            window_id = parts[0]
            window_title = parts[3].replace("EVE - ", "")
            window_dict[window_title] = window_id

        # Create ordered list of open windows based on character_list order
        ordered_windows = []
        for char_name in character_list:
            if char_name in window_dict:
                ordered_windows.append((window_dict[char_name], char_name))

        if not ordered_windows:
            logging.warning("No matching character windows open.")
            return

        # Cycle through windows in correct order
        if reverse:
            self.current_index = (self.current_index - 1) % len(ordered_windows)
        else:
            self.current_index = (self.current_index + 1) % len(ordered_windows)

        next_window_id, next_character_name = ordered_windows[self.current_index]

        logging.info(f"Switching to: {next_character_name} (Window ID: {next_window_id})")
        self.window_manager.set_last_active_client(next_window_id)
        self.focus_window(next_window_id)

    def list_windows(self):
        """List all open windows using `wmctrl`."""
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            return result.stdout.splitlines()
        except Exception as e:
            logging.error(f"Error listing windows: {e}")
            return []

    def focus_window(self, window_id):
        """Bring a window to the front using `wmctrl`."""
        logging.debug(f"🖥️ Attempting to bring window {window_id} to the front...")
        try:
            subprocess.run(['wmctrl', '-i', '-a', window_id])
            logging.info(f"Window {window_id} successfully brought to front.")
        except Exception as e:
            logging.error(f"Error bringing window {window_id} to front: {e}")

    def update_current_index(self, window_id):
        """
        Update the current index based on the active window,
        respecting the order in the character list.
        """
        # Get ordered character list from config
        character_list = list(self.main_window.config["hotkeys"]["character_list"].keys())
        
        # Get open windows
        open_windows = self.list_windows()
        eve_windows = [line for line in open_windows if "EVE - " in line]
        
        # Match window_id to character name
        target_char_name = None
        for window in eve_windows:
            parts = window.split(None, 3)
            if len(parts) < 4:
                continue
            win_id = parts[0]
            if win_id == window_id:
                target_char_name = parts[3].replace("EVE - ", "")
                break
        
        if not target_char_name:
            return
        
        # Create ordered list of open windows
        ordered_windows = []
        window_dict = {}
        for window in eve_windows:
            parts = window.split(None, 3)
            if len(parts) < 4:
                continue
            win_id = parts[0]
            char_name = parts[3].replace("EVE - ", "")
            window_dict[char_name] = win_id
        
        for char_name in character_list:
            if char_name in window_dict:
                ordered_windows.append((window_dict[char_name], char_name))
        
        # Find index of target window in ordered list
        for index, (win_id, char_name) in enumerate(ordered_windows):
            if char_name == target_char_name:
                self.current_index = index
                logging.debug(f"Updated current index to {index} ({char_name})")
                break