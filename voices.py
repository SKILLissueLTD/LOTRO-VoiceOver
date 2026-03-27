import os
import sys
import json
import hashlib
import subprocess
import time
import threading
import queue
import pygame
import unicodedata
import re
from utils import resource_path
import globalVariables
from getNPCGender import return_npc_gender
from ocr_spellcheck import fix_text_advanced

# -----------------------------
# PATHS
# -----------------------------

def get_base_dir():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def get_appdata_dir():
    path = os.path.join(os.getenv("APPDATA"), "LOTROVoiceover")
    os.makedirs(path, exist_ok=True)
    return path


def get_models_dir():
    appdata_models = os.path.join(get_appdata_dir(), "models")
    return appdata_models


BASE_DIR = get_base_dir()
APPDATA_DIR = get_appdata_dir()

CONFIG_PATH = os.path.join(APPDATA_DIR, "voice_config.json")
CACHE_DIR = os.path.join(APPDATA_DIR, "voice_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# -----------------------------
# PIPER + AUDIO INIT
# -----------------------------
try:
    PIPER_PATH = globalVariables.env.get("piper") or resource_path("piper/piper.exe")
except:
    PIPER_PATH = resource_path("piper/piper.exe")

if not os.path.exists(PIPER_PATH):
    print("[ERROR] Piper executable not found:", PIPER_PATH)

os.environ["ESPEAK_DATA_PATH"] = resource_path("espeak-ng-data")

# Safe pygame init (prevents crashes on some systems)
try:
    pygame.mixer.init()
except Exception as e:
    print("[AUDIO] Failed to init mixer:", e)
speech_queue = queue.Queue()

# -----------------------------
# GLOBAL STATE
# -----------------------------

if not hasattr(globalVariables, "paused"):
    globalVariables.paused = False

# -----------------------------
# STOP SYSTEM (IMPORTANT)
# -----------------------------

def clear_queue():
    try:
        while True:
            speech_queue.get_nowait()
            speech_queue.task_done()
    except queue.Empty:
        pass


def stop_all():
    globalVariables.paused = True

    try:
        pygame.mixer.stop()
    except:
        pass

    clear_queue()

    print("[VOICE] STOPPED + QUEUE CLEARED")


def resume():
    globalVariables.paused = False
    #print("[VOICE] RESUMED")

# -----------------------------S
# NORMALIZE
# -----------------------------

def normalize_name(name):
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = name.lower()

    # remove punctuation here too
    name = re.sub(r'[^a-z0-9 ]', '', name)

    return name.strip()

# -----------------------------
# NPC GENDER
# -----------------------------

NPC_FOLDER = os.path.join(BASE_DIR, "Helpful Stuffs", "NPCs")
NPC_FILES = ["npcsEN.txt", "npcsDE.txt", "npcsFR.txt"]

npc_gender_map = {}

def load_npc_gender_files():
    npc_gender_map.clear()

    for file in NPC_FILES:
        path = os.path.join(NPC_FOLDER, file)
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "[" not in line:
                    continue
                try:
                    name, gender = line.rsplit("[", 1)
                    gender = gender.replace("]", "").strip().lower()
                    name = normalize_name(name.strip())

                    if gender in ["m", "f"]:
                        npc_gender_map[name] = "male" if gender == "m" else "female"
                except:
                    continue

    print(f"[NPC] Loaded {len(npc_gender_map)} gender entries")

def get_gender_from_files(name):
    if not name:
        return None

    n = normalize_name(name)

    # 1. Exact match
    if n in npc_gender_map:
        return npc_gender_map[n]

    # 2. Clean common junk (VERY IMPORTANT)
    n_clean = re.sub(r'[^a-z0-9 ]', '', n)

    if n_clean in npc_gender_map:
        return npc_gender_map[n_clean]

    # 3. Fuzzy match (fallback)
    from difflib import get_close_matches

    matches = get_close_matches(n_clean, npc_gender_map.keys(), n=1, cutoff=0.85)

    if matches:
        return npc_gender_map[matches[0]]

    return None

# -----------------------------
# RACE TREE
# -----------------------------

RACE_FILE = os.path.join(NPC_FOLDER, "raceTree.txt")
npc_race_map = {}

def load_race_tree():
    npc_race_map.clear()

    if not os.path.exists(RACE_FILE):
        print("[RACE] raceTree missing")
        return

    with open(RACE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            name, race = line.strip().split("|", 1)
            npc_race_map[normalize_name(name)] = race.strip()

    print(f"[RACE] Loaded {len(npc_race_map)} entries")

# -----------------------------
# HOBBITS
# -----------------------------

HOBBIT_FILE = os.path.join(NPC_FOLDER, "hobbitFamilies.txt")
hobbit_names = set()

def load_hobbit_families():
    hobbit_names.clear()

    if not os.path.exists(HOBBIT_FILE):
        print("[HOBBIT] file missing")
        return

    with open(HOBBIT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            name = normalize_name(line.strip())
            if name:
                hobbit_names.add(name)

    print(f"[HOBBIT] Loaded {len(hobbit_names)} families")

# -----------------------------
# RACE DETECTION
# -----------------------------

def detect_race(name):

    if not name:
        return "human"

    # -----------------------------
    #  STEP 0
    # -----------------------------
    try:
        name = fix_text_advanced(name)
    except:
        pass

    n = normalize_name(name)
    parts = n.split()

    # -----------------------------
    # 1. EXACT raceTree match (STRONGEST)
    # -----------------------------
    if n in npc_race_map:
        return npc_race_map[n]

    # -----------------------------
    # 2. SPECIAL CHARACTERS (EXPLICIT)
    # -----------------------------
    if any(x in n for x in ["gandalf", "saruman", "radagast", "bombadil"]):
        return "wizard"

    # -----------------------------
    # 3. HOBBIT (VERY STRONG)
    # -----------------------------
    if any(part in hobbit_names for part in parts):
        return "hobbit"

    # -----------------------------
    # 4. MONSTERS / ORCS
    # -----------------------------
    if any(x in n for x in ["orc", "uruk", "goblin"]):
        return "human"

    if any(x in n for x in ["troll", "warg"]):
        return "human"

    # -----------------------------
    # 5. ELF DETECTION
    # -----------------------------

    # Strong Tolkien suffixes
    if re.search(r"(iel|riel|wen|loth|las|ion|dir|ndil|hir|eth|mir|nor|dil)$", n):
        return "elf"

    # Elvish phonetics (avoid short false positives)
    if len(n) > 6 and re.search(r"(ae|ia|ea|ui|gal|fin|thal|riel|wen|loth)", n):
        return "elf"

    # Known elf-related words
    if any(x in n for x in ["elf", "lorien", "imladris", "galadhrim"]):
        return "elf"

    # -----------------------------
    # 6. DWARF DETECTION
    # -----------------------------

    # Strong known dwarf names/parts
    if any(x in n for x in [
        "gimli","durin","bofur","bombur","thorin","dwalin","balin",
        "gisi","glin","fli","frerin","fundin","ori","thrain",
        "telchar","oin","dori","nori","borin","bifur","nar",
        "narvi","nain","dain","gror","kili","fili","loin","gloin"
    ]):
        return "dwarf"

    # Classic suffixes
    if re.search(r"(in|ar|ur|ain|orn|ori|oin)$", n):
        return "dwarf"

    # Short Norse-style dwarf names (VERY IMPORTANT FIX)
    if re.fullmatch(r"[a-z]{3,5}", n) and re.search(r"(i|o|u)$", n):
        return "dwarf"

    # Dwarf keywords
    if any(x in n for x in ["dwarf","longbeard","stoutaxe","iron","stone","hammer","anvil"]):
        return "dwarf"

    # -----------------------------
    # 7. FALLBACK
    # -----------------------------
    return "human"

# -----------------------------
# INIT LOAD
# -----------------------------

load_npc_gender_files()
load_race_tree()
load_hobbit_families()

# -----------------------------
# CONFIG
# -----------------------------

_config_cache = None
_config_mtime = 0

def get_config():
    global _config_cache, _config_mtime

    if not os.path.exists(CONFIG_PATH):
        return {"races": {}}

    mtime = os.path.getmtime(CONFIG_PATH)

    if _config_cache is None or mtime != _config_mtime:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                _config_cache = json.load(f)
                _config_mtime = mtime
        except:
            _config_cache = {"races": {}}

    return _config_cache

# -----------------------------
# MODEL
# -----------------------------

def resolve_model_path(path):
    if not path:
        return None

    path = path.replace("\\", "/")

    if not os.path.isabs(path):
        path = os.path.join(get_models_dir(), path)

    path = os.path.normpath(path)

    return path if os.path.isfile(path) else None

def get_fallback_model(race, gender):
    models_dir = get_models_dir()
    root_model = os.path.join(models_dir, "en_US-libritts-high.onnx")
    if os.path.isfile(root_model):
        return root_model
    return None

def get_voice_config(race, gender):
    cfg = get_config()
    data = cfg.get("races", {}).get(race, {}).get(gender, {})

    model_path = resolve_model_path(data.get("model_path"))

    if not model_path:
        model_path = get_fallback_model(race, gender)

    if not model_path:
        print("[ERROR] No model found at all")
        return None, None, {}

    speaker = data.get("speaker_id") if data.get("use_speaker_id") else None
    emotion = data.get("emotion", {})

    return model_path, speaker, emotion

# -----------------------------
# GENERATE
# -----------------------------
def get_npc_override(name):
    cfg = get_config()
    return cfg.get("npc_overrides", {}).get(normalize_name(name))


def generate(text, output, npc):

    override = get_npc_override(npc)

    if override:
        race = "human"
        gender = "male"

        base_model, _, _ = get_voice_config(race, gender)

        model_path = resolve_model_path(override.get("model_path"))
        if not model_path:
            model_path = base_model

        speaker = override.get("speaker_id")
        emotion = override.get("emotion", {})

    else:
        race = detect_race(npc)
        gender = get_gender_from_files(npc)

        if not gender:
            gender = return_npc_gender(npc) or "male"

        model_path, speaker, emotion = get_voice_config(race, gender)

    if not emotion:
        emotion = {}

    print(f"[GENDER DEBUG] NPC='{npc}' → gender='{gender}'")

    if not model_path:
        print("[ERROR] No model found")
        return

    if globalVariables.debug_mode:
        print(f"[DEBUG] NPC: {npc}")
        print(f"[DEBUG] Race: {race}, Gender: {gender}")
        print(f"[DEBUG] Model: {model_path}, Speaker: {speaker}, Emotion: {emotion}")

    speed = emotion.get("speed", 1.0) / globalVariables.reading_speed
    noise = emotion.get("noise", 0.6)

    cmd = [
        PIPER_PATH,
        "--model", model_path,
        "--output_file", output,
        "--length-scale", str(speed),
        "--noise-scale", str(noise),
        "--noise-w", "0.75"
    ]

    if speaker is not None and speaker != -1:
        cmd += ["--speaker", str(speaker)]

    try:
        subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print("[PIPER ERROR]", e)

# -----------------------------
# WORKER
# -----------------------------

def speech_worker():
    while True:

        if globalVariables.paused:
            time.sleep(0.1)
            continue

        text, npc = speech_queue.get()

        try:
            output = os.path.join(
                CACHE_DIR,
                hashlib.md5((npc + text).encode()).hexdigest() + ".wav"
            )

            # 🔥 fix corrupted cache
            if os.path.exists(output) and os.path.getsize(output) < 2000:
                os.remove(output)

            if not os.path.exists(output):
                generate(text, output, npc)

            if os.path.exists(output):
                sound = pygame.mixer.Sound(output)
                sound.play()

                while pygame.mixer.get_busy():
                    if globalVariables.paused:
                        pygame.mixer.stop()
                        break
                    time.sleep(0.05)

        except Exception as e:
            print("[VOICE ERROR]", e)

        finally:
            speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

# -----------------------------
# PUBLIC API
# -----------------------------

def speak(text, npc="Narrator"):

    if globalVariables.paused or not text:
        return

    sentences = re.split(r'(?<=[.!?])\s+', text)

    for s in sentences:
        s = s.strip()
        if len(s) > 2:
            speech_queue.put((s, npc))