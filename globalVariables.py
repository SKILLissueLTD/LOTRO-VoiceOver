import sys
from pathlib import Path


# -----------------------------
# Runtime flags
# -----------------------------

already_talked = False
enable_disable = True  # default ON (matches tray)

paused = False
tts_queue = []
tts_playing = False

recent_lines = []  # [{"text": ..., "time": ...}]
last_spoken = {}

only_narrate_book_quests = False # <-- this must be True
is_book_quest = True

debug_mode = False

# UI scaling
scan_ui_scale = True          # allow scanning
ui_scale = None               # detected scale
ui_scale_scanning_active = False  # currently scanning

# App version (keep updated manually)
app_version = "0.1.2"
# GitHub repository slug for update checks (owner/repo)
github_repo = "SKILLissueLTD/lotro-voiceover"

use_script_log = True

# -----------------------------
# Speech settings
# -----------------------------

reading_speed = 1.0  # global multiplier (0.5 → 2.0)


# -----------------------------
# OCR data
# -----------------------------

text_ocr = ""
title_ocr = ""
tesseract_language = ""


# -----------------------------
# Coordinates
# -----------------------------

start_x = None
start_y = None
end_x = None
end_y = None


# -----------------------------
# Voice config (legacy / optional)
# -----------------------------

character_rate = {
    "default": "1.0",
    "narrator": "0.9",
    "hero": "1.2",
    "villain": "0.8"
}

character_emphasis = {
    "default": False,
    "narrator": False,
    "hero": True,
    "villain": True
}

character_breaks = {
    "default": "300ms",
    "narrator": "500ms",
    "hero": "200ms",
    "villain": "600ms"
}

character_volume = {
    "default": "default",
    "whisper": "x-soft",
    "yell": "x-loud"
}


# -----------------------------
# Paths (EXE SAFE)
# -----------------------------

def get_base_path():
    """
    Works in both:
    - dev (python)
    - PyInstaller EXE
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.resolve()


BASE_DIR = get_base_path()

audio_path_string = str(BASE_DIR / "LOTROToSpeech" / "Audios")
config_path = str(BASE_DIR / "LOTROToSpeech" / "Configs")
image_detection_path = str(BASE_DIR / "LOTROToSpeech" / "Detection")
voices_path = str(BASE_DIR / "LOTROToSpeech" / "Voices")