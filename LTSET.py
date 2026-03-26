print("=== LTSET STARTED ===")

# -----------------------------
# IMPORTS (needed early)
# -----------------------------
import threading
import globalVariables
from loading_ui import LoadingUI

# -----------------------------
# SETUP (RUN ASYNC)
# -----------------------------
from setup_manager import run_setup, is_setup_required

print("[INIT] Checking dependencies (first launch may take ~10-20s)...")

env = None


# -----------------------------
# SETUP THREAD (DEFINE FIRST!)
# -----------------------------
def setup_thread():
    global env

    try:
        loading_ui.set_text("Preparing system...")
        loading_ui.set_progress(0)

        # -----------------------------
        # PROGRESS + STATUS HOOKS
        # -----------------------------
        def on_progress(p):
            loading_ui.set_progress(int(p))

        def on_status(text):
            loading_ui.set_text(text)

        # 🔥 NEW: speed + ETA
        def on_stats(downloaded, total):
            loading_ui.update_download_stats(downloaded, total)

        env = run_setup(
            progress_callback=on_progress,
            status_callback=on_status,
            stats_callback=on_stats   # 👈 IMPORTANT
        )

        # -----------------------------
        # FINALIZE
        # -----------------------------
        loading_ui.set_text("Finalizing...")
        loading_ui.set_progress(100)

        globalVariables.env = env

        loading_ui.finish()

        print("[INIT] Setup complete")

    except Exception as e:
        print("[INIT ERROR]", e)
        loading_ui.set_text("Setup failed ❌")
        loading_ui.close()


# -----------------------------
# CONDITIONAL SETUP START
# -----------------------------
# --------------------------------
# SETUP PHASE (runs first)
# --------------------------------
if is_setup_required():
    print("[INIT] First run → showing setup UI")

    loading_ui = LoadingUI()

    t = threading.Thread(target=setup_thread, daemon=True)
    t.start()

    loading_ui.run()

    print("[INIT] Setup UI closed → continuing startup")

else:
    print("[INIT] Setup already complete → silent start")

    env = run_setup()
    globalVariables.env = env


# -----------------------------
# IMPORTS
# -----------------------------
from utils import resource_path
import asyncio
import createAllFilesAndDirectories
import lookForTesseract
import OCRDetectionAndCleanup
import piperTTSEngine
import keyboard
import pystray
from PIL import Image
import os
import time
import sys
import shutil
import urllib.request
import urllib.error
import re
from quest_popup import popup
import tkinter as tk
from tkinter import messagebox
import json
from voice_config_ui import open_window as open_voice_config
import voices
from script_log_reader import ScriptLogReader

# -----------------------------
# PATHS
# -----------------------------
def get_appdata_dir():
    path = os.path.join(os.getenv("APPDATA"), "LOTROVoiceover")
    os.makedirs(path, exist_ok=True)
    return path


APPDATA_DIR = get_appdata_dir()

# -----------------------------
# DEFAULTS
# -----------------------------

globalVariables.enable_disable = True
globalVariables.reading_speed = 1.0
globalVariables.only_narrate_book_quests = False
globalVariables.debug_mode = False
globalVariables.scan_ui_scale = True


# -----------------------------
# SETUP
# -----------------------------

def setup():
    createAllFilesAndDirectories.create()
    lookForTesseract.look_for_tesseract()
    copy_required_plugin()

    # Ensure models folder exists in AppData
    ensure_models_in_appdata()
    
    # Load saved UI scale if it exists
    scale_file = os.path.join(APPDATA_DIR, "ui_scale.txt")
    if os.path.exists(scale_file):
        try:
            with open(scale_file, "r") as f:
                saved_scale = float(f.read().strip())
            globalVariables.ui_scale = saved_scale
            globalVariables.scan_ui_scale = False  # Don't scan if we already have the scale
            print(f"[SETUP] Loaded UI scale: {saved_scale:.2f}")
        except:
            # If load fails, start scanning
            globalVariables.scan_ui_scale = True
            print("[SETUP] UI scale file invalid, will scan")
    else:
        # First time setup
        globalVariables.scan_ui_scale = True
        print("[SETUP] First startup, will scan for UI scale")

    threading.Thread(target=check_for_updates, daemon=True).start()

# -------- ---------------------
# COPY REGUIRED PLUGINS TO GAME FOLDER IN DOCUMENTS
# -------- ---------------------
def copy_required_plugin():
    """
    Copy Required Plugin contents into LOTRO Plugins folder
    with full debug output.
    """

    try:
        print("=== PLUGIN COPY START ===")

        # -------------------------
        # SOURCE
        # -------------------------
        src = resource_path("Resources/Required Plugin")
        print("[PLUGIN] Source path:", src)

        if not os.path.exists(src):
            print("[PLUGIN] ❌ Source does NOT exist")
            return

        print("[PLUGIN] Source exists")

        # -------------------------
        # DESTINATION
        # -------------------------
        documents = os.path.join(os.path.expanduser("~"), "Documents")
        lotro_folder = os.path.join(documents, "The Lord of the Rings Online")
        plugins_folder = os.path.join(lotro_folder, "Plugins")

        print("[PLUGIN] Destination:", plugins_folder)

        os.makedirs(plugins_folder, exist_ok=True)

        # -------------------------
        # LIST FILES
        # -------------------------
        items = os.listdir(src)

        if not items:
            print("[PLUGIN] ❌ Source folder is EMPTY")
            return

        print(f"[PLUGIN] Found {len(items)} items")

        # -------------------------
        # COPY LOOP
        # -------------------------
        for item in items:

            s = os.path.join(src, item)
            d = os.path.join(plugins_folder, item)

            print(f"[PLUGIN] Copying: {item}")

            if os.path.isdir(s):
                print(f"[PLUGIN] Dir -> {d}")

                if not os.path.exists(d):
                    shutil.copytree(s, d)
                else:
                    print("[PLUGIN] Merging existing folder")

                    for root, dirs, files in os.walk(s):
                        rel = os.path.relpath(root, s)
                        dest_dir = os.path.join(d, rel)

                        os.makedirs(dest_dir, exist_ok=True)

                        for f in files:
                            src_file = os.path.join(root, f)
                            dst_file = os.path.join(dest_dir, f)

                            shutil.copy2(src_file, dst_file)

            else:
                print(f"[PLUGIN] File -> {d}")
                shutil.copy2(s, d)

        print("[PLUGIN] ✅ COPY DONE")

    except Exception as e:
        print(f"[PLUGIN] ❌ FAILED:", e)
# -------- ---------------------
# COPY MODELS TO APPDATA
# -------- ---------------------

def ensure_models_in_appdata():
    """Ensure models + folder structure exist in AppData"""

    appdata_models = os.path.join(APPDATA_DIR, "models")
    bundle_models = resource_path("models")

    os.makedirs(appdata_models, exist_ok=True)

    # -----------------------------
    # CHECK MODEL EXISTS
    # -----------------------------
    model_exists = os.path.exists(
        os.path.join(appdata_models, "en_US-libritts-high.onnx")
    )

    # -----------------------------
    # COPY IF NEEDED
    # -----------------------------
    if not model_exists:
        if os.path.isdir(bundle_models):
            print("[SETUP] Copying models from bundle to AppData...")
            try:
                shutil.copytree(bundle_models, appdata_models, dirs_exist_ok=True)
                print(f"[SETUP] Models copied to: {appdata_models}")
            except Exception as e:
                print(f"[SETUP] Failed to copy models: {e}")
        else:
            print("[SETUP] No models folder found in bundle (using downloader)")
    else:
        print("[SETUP] Model already installed")

    # -----------------------------
    # ALWAYS CREATE STRUCTURE
    # -----------------------------
    print("[SETUP] Ensuring model folder structure...")

    expected = [
        ("elf", "male"),
        ("elf", "female"),
        ("human", "male"),
        ("human", "female"),
        ("hobbit", "male"),
        ("hobbit", "female"),
        ("dwarf", "male"),
        ("dwarf", "female"),
    ]

    for race, gender in expected:
        path = os.path.join(appdata_models, race, gender)
        os.makedirs(path, exist_ok=True)

    # -----------------------------
    # COPY voice_config.json ON FIRST RUN
    # -----------------------------
    appdata_config = os.path.join(APPDATA_DIR, "voice_config.json")
    bundle_config = resource_path("voice_config.json")

    if not os.path.exists(appdata_config):
        try:
            shutil.copy2(bundle_config, appdata_config)
            print("[SETUP] voice_config.json copied to AppData")
        except Exception as e:
            print(f"[SETUP] Failed to copy voice_config.json: {e}")
    else:
        print("[SETUP] voice_config.json already exists (skipped)")


def normalize_version(v):
    parts = re.findall(r"\d+", str(v))
    return tuple(int(x) for x in parts)


def is_newer_version(current, latest):
    try:
        return normalize_version(latest) > normalize_version(current)
    except:
        return False


def get_latest_github_version(repo):
    if not repo or repo == "SKILLissueLTD/LOTRO-VoiceOver":
        return None

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LOTROVoiceover"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))

        tag_name = data.get("tag_name") or data.get("name")

        if tag_name:
            return str(tag_name).lstrip("v")

    except urllib.error.URLError:
        return None
    except Exception as e:
        print(f"[UPDATE] Failed to fetch latest release: {e}")
        return None


def check_for_updates():
    latest_version = get_latest_github_version(globalVariables.github_repo)

    if not latest_version:
        return

    if is_newer_version(globalVariables.app_version, latest_version):
        msg = (f"New version available: {latest_version} (current {globalVariables.app_version}). "
               f"Visit GitHub to download.")
        print(f"[UPDATE] {msg}")

        try:
            messagebox.showinfo("LOTRO Voiceover Update", msg)
        except Exception:
            pass


# -----------------------------
# OCR LOOP
# -----------------------------
async def monitor_loop_async():
    print("[MONITOR] HYBRID MODE (continuous OCR + log trigger boost)")

    log_path = os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "The Lord of the Rings Online",
        "Script.log"
    )

    reader = ScriptLogReader(log_path)

    # -----------------------------
    # WAIT FOR FILE (BUT NOT FOREVER)
    # -----------------------------
    log_available = False
    wait_time = 0

    print("[LOG] Checking for Script.log...")

    while wait_time < 5:
        if os.path.exists(log_path):
            log_available = True
            print("[LOG] Script.log detected → trigger enabled")
            reader.wait_for_file()
            break

        await asyncio.sleep(1)
        wait_time += 1

    if not log_available:
        print("[LOG] Script.log not found → OCR only mode")

    last_lines = []
    last_ocr_text = ""

    while True:

        # -----------------------------
        # WAIT FOR SETUP
        # -----------------------------
        if not getattr(globalVariables, "env", None):
            await asyncio.sleep(0.2)
            continue

        try:
            # =============================
            # 🔵 SCRIPT.LOG (OPTIONAL BOOST)
            # =============================
            if log_available:

                new_lines = reader.read_new_lines()

                for line in new_lines:

                    if not line.strip():
                        continue

                    # avoid duplicate spam
                    if last_lines and line == last_lines[-1]:
                        continue

                    print(f"[LOG] Trigger: {line}")

                    last_lines.append(line)
                    if len(last_lines) > 50:
                        last_lines.pop(0)

                    # 🔥 optional: wake voice system
                    voices.resume()

            # =============================
            # 🟡 OCR (ALWAYS RUNS)
            # =============================
            if OCRDetectionAndCleanup.ocr_detection_and_cleaup():

                text = globalVariables.text_ocr.strip()

                # skip garbage only
                if not text or len(text) < 3:
                    await asyncio.sleep(0.05)
                    continue

                # 🔥 smarter duplicate handling
                if text == last_ocr_text:
                    # do NOT block speech system — just skip re-speaking
                    await asyncio.sleep(0.05)
                    continue

                print(f"[OCR] {text}")

                last_ocr_text = text

                voices.resume()

                if globalVariables.enable_disable:

                    if globalVariables.only_narrate_book_quests and not globalVariables.is_book_quest:
                        pass
                    else:
                        await piperTTSEngine.tts_engine(text)

            # =============================
            # SPEED (FAST + RESPONSIVE)
            # =============================
            await asyncio.sleep(0.05)

        except Exception as e:
            print("[MONITOR ERROR]", e)
            await asyncio.sleep(1)


# -----------------------------
# TRAY GLOBAL
# -----------------------------

tray_icon = None


def refresh_tray():
    global tray_icon
    if tray_icon:
        tray_icon.menu = build_menu()


# -----------------------------
# TRAY ACTIONS
# -----------------------------

def tray_quit(icon, item):
    try:
        icon.stop()
    except:
        pass
    os._exit(0)


def toggle_voiceover(icon=None, item=None):
    globalVariables.enable_disable = not globalVariables.enable_disable
    print("Voiceover:", globalVariables.enable_disable)
    refresh_tray()


def stop_speaking(icon=None, item=None):
    try:
        voices.stop_all()
    except Exception as e:
        print("[STOP ERROR]", e)
    refresh_tray()


def toggle_popup(icon, item):
    try:
        popup.toggle_popup()
    except:
        pass
    refresh_tray()


def toggle_book_quest_only(icon, item):
    globalVariables.only_narrate_book_quests = not globalVariables.only_narrate_book_quests
    refresh_tray()


def toggle_debug(icon, item):
    globalVariables.debug_mode = not globalVariables.debug_mode
    refresh_tray()


# -----------------------------
# CACHE
# -----------------------------

def clear_cache():
    cache_dir = os.path.join(APPDATA_DIR, "voice_cache")

    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            try:
                os.remove(os.path.join(cache_dir, f))
            except:
                pass

    print("Cache cleared")


# -----------------------------
# SPEED
# -----------------------------

def set_speed(speed):
    globalVariables.reading_speed = speed
    clear_cache()
    refresh_tray()


# -----------------------------
# UI TOOLS
# -----------------------------

def reset_ui_scale(icon=None, item=None):
    globalVariables.ui_scale = None
    globalVariables.scan_ui_scale = True
    
    # Delete saved scale file
    scale_file = os.path.join(APPDATA_DIR, "ui_scale.txt")
    try:
        if os.path.exists(scale_file):
            os.remove(scale_file)
    except:
        pass
    
    clear_cache()
    refresh_tray()
    print("[RESET] UI scale reset, will rescan")


def open_models_folder(icon, item):
    # Open the AppData config folder (contains models, configs, cache, etc.)
    if os.path.exists(APPDATA_DIR):
        os.startfile(APPDATA_DIR)
    else:
        print("[ERROR] AppData folder not found")


# -----------------------------
# VOICE SETTINGS
# -----------------------------

def open_voice_settings(icon, item):
    threading.Thread(target=open_voice_config, daemon=True).start()


# -----------------------------
# HOTKEY WINDOW (FIXED)
# -----------------------------

def open_hotkey_window(icon=None, item=None):

    root = tk._default_root
    if root is None:
        root = tk.Tk()
        root.withdraw()

    win = tk.Toplevel(root)
    win.title("Hotkeys")
    win.geometry("360x360")


    config_file = os.path.join(APPDATA_DIR, "hotkeys.json")

    def capture(entry):

        entry.delete(0, tk.END)
        entry.insert(0, "Listening...")

        pressed = set()

        def on_press(e):
            pressed.add(e.name)

        def on_release(e):
            combo = "+".join(sorted(pressed))
            entry.delete(0, tk.END)
            entry.insert(0, combo)
            keyboard.unhook_all()

        keyboard.hook(on_press)
        keyboard.on_release(on_release)

    def row(label):
        tk.Label(win, text=label).pack()
        e = tk.Entry(win)
        e.pack()
        tk.Button(win, text="Set Key", command=lambda: capture(e)).pack(pady=3)
        return e

    toggle = row("Toggle Voiceover")
    stop = row("Stop Speaking")
    reset = row("Reset UI Scale")

    try:
        with open(config_file) as f:
            data = json.load(f)
            toggle.insert(0, data.get("toggle", "shift+v"))
            stop.insert(0, data.get("stop", "shift+s"))
            reset.insert(0, data.get("reset", "shift+r"))
    except:
        pass

    def save():

        data = {
            "toggle": toggle.get(),
            "stop": stop.get(),
            "reset": reset.get()
        }

        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)

        load_hotkeys()
        refresh_tray()

        win.destroy()

    tk.Button(win, text="Save", command=save).pack(pady=(10, 15))


# -----------------------------
# HOTKEYS LOAD
# -----------------------------

def load_hotkeys():

    keyboard.unhook_all()

    config_file = os.path.join(APPDATA_DIR, "hotkeys.json")

    default_keys = {
        "toggle": "shift+v",
        "stop": "shift+s",
        "reset": "shift+r"
    }

    if not os.path.exists(config_file):
        os.makedirs(APPDATA_DIR, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_keys, f, indent=2)
        data = default_keys
        print("[HOTKEYS] Default hotkeys written to AppData")
    else:
        try:
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = default_keys

    updated = False
    for key, value in default_keys.items():
        if not data.get(key):
            data[key] = value
            updated = True

    if updated:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("[HOTKEYS] Added missing hotkeys to AppData hotkeys.json")
    try:
        keyboard.add_hotkey(data["toggle"], lambda: toggle_voiceover())
    except Exception as e:
        print("[HOTKEY ERROR]", e)
    try:
        keyboard.add_hotkey(data["stop"], lambda: stop_speaking())
    except Exception as e:
        print("[HOTKEY ERROR]", e)
    try:
        keyboard.add_hotkey(data["reset"], lambda: reset_ui_scale())
    except Exception as e:
        print("[HOTKEY ERROR]", e)


def get_hotkey_text():
    config_file = os.path.join(APPDATA_DIR, "hotkeys.json")

    try:
        with open(config_file) as f:
            data = json.load(f)
            return f"Toggle: {data['toggle']} | Stop: {data['stop']}"
    except:
        return "Hotkeys not set"


# -----------------------------
# TRAY
# -----------------------------

def setup_tray():
    global tray_icon

    icon_path = resource_path("resources/lotrotospeech.ico")

    if not os.path.exists(icon_path):
        image = Image.new("RGB", (64, 64), color=(50, 50, 50))
    else:
        image = Image.open(icon_path)

    tray_icon = pystray.Icon("LOTROVoice", image, "LOTRO Voiceover")
    tray_icon.menu = build_menu()
    tray_icon.run()


def build_menu():

    return pystray.Menu(

        pystray.MenuItem(
            "Enable Voiceover",
            toggle_voiceover,
            checked=lambda i: globalVariables.enable_disable
        ),

        pystray.MenuItem("Stop Speaking", stop_speaking),

        pystray.Menu.SEPARATOR,

        pystray.MenuItem("Reading Speed", pystray.Menu(
            pystray.MenuItem("Very Slow", lambda i, x: set_speed(0.5),
                             checked=lambda i: globalVariables.reading_speed == 0.5),
            pystray.MenuItem("Slow", lambda i, x: set_speed(0.75),
                             checked=lambda i: globalVariables.reading_speed == 0.75),
            pystray.MenuItem("Default", lambda i, x: set_speed(1.0),
                             checked=lambda i: globalVariables.reading_speed == 1.0),
            pystray.MenuItem("Fast", lambda i, x: set_speed(1.25),
                             checked=lambda i: globalVariables.reading_speed == 1.25),
            pystray.MenuItem("Very Fast", lambda i, x: set_speed(1.5),
                             checked=lambda i: globalVariables.reading_speed == 1.5),
            pystray.MenuItem("Fastest", lambda i, x: set_speed(2.0),
                             checked=lambda i: globalVariables.reading_speed == 2.0),
        )),

        pystray.Menu.SEPARATOR,

        pystray.MenuItem("Voice Settings", open_voice_settings),

        pystray.Menu.SEPARATOR,

        pystray.MenuItem("Quest Window", toggle_popup,
                         checked=lambda i: popup.popup_enabled),

        pystray.MenuItem("Book Quests Only", toggle_book_quest_only,
                         checked=lambda i: globalVariables.only_narrate_book_quests),

        pystray.MenuItem("Debug Mode", toggle_debug,
                         checked=lambda i: globalVariables.debug_mode),

        pystray.MenuItem("Reset UI Scale", reset_ui_scale),

        pystray.MenuItem("Clear Cache", lambda i, x: clear_cache()),

        pystray.MenuItem("Open Config Folder", open_models_folder),

        pystray.MenuItem("Hotkey Settings", open_hotkey_window),

        pystray.Menu.SEPARATOR,

        pystray.MenuItem("Exit", tray_quit)
    )
# --------------------------------
# MAIN APP STARTS ONLY AFTER SETUP
# --------------------------------
if __name__ == "__main__":

    setup()
    load_hotkeys()

    tray_thread = threading.Thread(
        target=setup_tray,
        daemon=True
    )
    tray_thread.start()

    monitor_thread = threading.Thread(
        target=lambda: asyncio.run(monitor_loop_async()),
        daemon=True
    )
    monitor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        os._exit(0)