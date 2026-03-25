from utils import resource_path
import pystray
from pystray import MenuItem as item
from PIL import Image
import globalVariables
import piperTTSEngine
import os
import threading

from voice_config_ui import open_window as open_voice_config


# -----------------------------
# PATHS (EXE SAFE)
# -----------------------------

def get_appdata_cache():
    path = os.path.join(os.getenv("APPDATA"), "LOTROVoiceover", "voice_cache")
    os.makedirs(path, exist_ok=True)
    return path


# -----------------------------
# Actions
# -----------------------------

def toggle_voiceover(icon, menu_item):
    globalVariables.enable_disable = not globalVariables.enable_disable
    state = "ON" if globalVariables.enable_disable else "OFF"
    print(f"[Tray] Voiceover {state}")


def stop_speaking(icon, menu_item):
    try:
        piperTTSEngine.stop_audio()
        print("[Tray] Speech stopped")
    except Exception as e:
        print("[Tray ERROR]", e)


def clear_cache(icon, menu_item):
    cache_dir = get_appdata_cache()

    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            try:
                os.remove(os.path.join(cache_dir, f))
            except:
                pass

    print("[Tray] Cache cleared")


def set_speed(value):
    def inner(icon, item):
        globalVariables.reading_speed = value
        clear_cache(icon, item)
        print(f"[Tray] Speed set to {value}")
    return inner


def toggle_debug(icon, item):
    globalVariables.debug_mode = not globalVariables.debug_mode
    print("[Tray] Debug:", globalVariables.debug_mode)


def quit_app(icon, item):
    print("[Tray] Exiting...")
    icon.stop()
    os._exit(0)


# -----------------------------
# VOICE CONFIG (SAME STYLE)
# -----------------------------

def open_voice_settings(icon, item):
    threading.Thread(target=open_voice_config, daemon=True).start()


# -----------------------------
# Tray
# -----------------------------

def run_tray():

    icon_path = resource_path("resources/lotrotospeech.ico")

    if not os.path.exists(icon_path):
        print("[WARNING] Icon not found, using fallback")
        image = Image.new("RGB", (64, 64), color=(50, 50, 50))
    else:
        image = Image.open(icon_path)

    menu = pystray.Menu(

        item(
            "Enable Voiceover",
            toggle_voiceover,
            checked=lambda item: globalVariables.enable_disable
        ),

        item("Stop Speaking", stop_speaking),

        pystray.Menu.SEPARATOR,

        item("Reading Speed", pystray.Menu(
            item("Very Slow (0.5)", set_speed(0.5)),
            item("Slow (0.75)", set_speed(0.75)),
            item("Default (1.0)", set_speed(1.0)),
            item("Fast (1.25)", set_speed(1.25)),
            item("Very Fast (1.5)", set_speed(1.5)),
            item("Fastest (2.0)", set_speed(2.0)),
        )),

        pystray.Menu.SEPARATOR,

        # ✅ SAME STYLE AS DEBUG / UI SCAN
        item(
            "Voice Settings",
            open_voice_settings
        ),

        pystray.Menu.SEPARATOR,

        item(
            "Debug Mode",
            toggle_debug,
            checked=lambda item: globalVariables.debug_mode
        ),

        item("Clear Cache", clear_cache),

        pystray.Menu.SEPARATOR,

        item("Quit", quit_app)
    )

    icon = pystray.Icon(
        "LOTRO Voiceover",
        image,
        "LOTRO Voiceover",
        menu
    )

    icon.run()