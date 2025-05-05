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
        """Cycle through the list of characters, skipping non-open ones."""
        logging.debug("Cycling characters...")

        # Get character names from the UI
        character_list = self.main_window.tabs.widget(4).get_character_list()
        logging.debug(f"Character list from UI: {character_list}")

        # Get a list of currently open EVE windows using `wmctrl`
        open_windows = self.list_windows()
        eve_windows = [line for line in open_windows if "EVE - " in line]
        logging.debug(f"Open EVE Windows: {eve_windows}")

        open_character_windows = []
        for window in eve_windows:
            parts = window.split(None, 3)
            if len(parts) < 4:
                continue
            window_id = parts[0]
            window_title = parts[3].replace("EVE - ", "")  

            if window_title in character_list:
                open_character_windows.append((window_id, window_title))

        if not open_character_windows:
            logging.warning("No matching character windows open.")
            return

        # Cycle to the next open character
        if reverse:
            self.current_index = (self.current_index - 1) % len(open_character_windows)
        else:
            self.current_index = (self.current_index + 1) % len(open_character_windows)

        next_window_id, next_character_name = open_character_windows[self.current_index]

        logging.info(f"Switching to: {next_character_name} (Window ID: {next_window_id})")
        self.window_manager.set_last_active_client(next_window_id)  # Set last active client
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
        """Update the current index based on the active window."""
        open_windows = self.list_windows()
        eve_windows = [line for line in open_windows if "EVE - " in line]

        open_character_windows = []
        for window in eve_windows:
            parts = window.split(None, 3)
            if len(parts) < 4:
                continue
            win_id = parts[0]
            window_title = parts[3].replace("EVE - ", "")

            if window_title in self.main_window.tabs.widget(4).get_character_list():
                open_character_windows.append((win_id, window_title))

        for index, (win_id, _) in enumerate(open_character_windows):
            if win_id == window_id:
                self.current_index = index
                break