from utils import resource_path
import keyboard
import voices
import config

def toggle_voice():

    config.voice_enabled = not config.voice_enabled

def stop_speech():

    voices.stop_current_audio()

def reset_ui_scale():

    config.ui_scale = None
    print("UI scale reset")

keyboard.add_hotkey("ctrl+shift+v", toggle_voice)
keyboard.add_hotkey("ctrl+shift+x", stop_speech)
keyboard.add_hotkey("ctrl+shift+r", reset_ui_scale)