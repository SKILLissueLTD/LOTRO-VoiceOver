import keyboard
import voices
import config
import json
import os
if __name__ == "__main__":

    print("=== MAIN START ===")

    setup()
    load_hotkeys()

    print("=== STARTING THREADS ===")

# -----------------------------
# Actions
# -----------------------------

def toggle_voice():

    config.voice_enabled = not config.voice_enabled

    state = "ON" if config.voice_enabled else "OFF"

    print(f"[Hotkey] Voiceover {state}")


def stop_speech():

    try:
        voices.stop_audio()
    except:
        pass

    print("[Hotkey] Speech stopped")


def reset_ui_scale():

    config.ui_scale = None

    # also clear cache (important)
    cache_dir = os.path.join(os.getcwd(), "voice_cache")

    if os.path.exists(cache_dir):

        for f in os.listdir(cache_dir):
            try:
                os.remove(os.path.join(cache_dir, f))
            except:
                pass

    print("[Hotkey] UI scale reset + cache cleared")


# -----------------------------
# Load Hotkeys
# -----------------------------

def load_hotkeys():

    config_file = os.path.join(os.getcwd(), "hotkeys.json")

    try:

        with open(config_file) as f:
            data = json.load(f)

    except:

        # defaults
        data = {
            "toggle": "shift+v",
            "stop": "shift+s",
            "reset": "shift+r"
        }

    print("[Hotkey] Loaded:", data)

    keyboard.add_hotkey(data["toggle"], toggle_voice)
    keyboard.add_hotkey(data["stop"], stop_speech)
    keyboard.add_hotkey(data["reset"], reset_ui_scale)


# -----------------------------
# Init
# -----------------------------

load_hotkeys()

print("[Hotkey] System ready")