# sudo python3 listener.py
import keyboard                 # pip install keyboard

def on_key(e):
    if e.event_type == 'down':  # key down only
        print(e.name, e.scan_code)

keyboard.hook(on_key)           # attach a global listener
keyboard.wait()                 # block forever
