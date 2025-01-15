import evdev

# Define the keyboard input device (replace if needed)
DEVICE_PATH = "/dev/input/event12"

def listen_for_tab():
    """Listens for the Tab key press using evdev."""
    try:
        device = evdev.InputDevice(DEVICE_PATH)
        print(f"Listening for Tab key on {DEVICE_PATH} ({device.name})...")

        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                key_code = key_event.scancode  # Get key code
                key_state = key_event.keystate  # 0 = release, 1 = press, 2 = hold

                if key_code == evdev.ecodes.KEY_TAB:
                    if key_state == 1:
                        print("Tab key detected!")
                    elif key_state == 0:
                        print("Tab key released.")

    except PermissionError:
        print(f"Permission denied. Try running with sudo:\n  sudo python {__file__}")
    except FileNotFoundError:
        print(f"Device {DEVICE_PATH} not found. Use `python -m evdev.evtest` to find the correct device.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    listen_for_tab()
