import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import json
import pygame
import sys
import time
from utils import resource_path


# -----------------------------
# PATHS
# -----------------------------

def get_base_dir():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_appdata_dir():
    path = os.path.join(os.getenv("APPDATA"), "LOTROVoiceover")
    os.makedirs(path, exist_ok=True)
    return path


BASE_DIR = get_base_dir()
APPDATA_DIR = get_appdata_dir()

CONFIG_PATH = os.path.join(APPDATA_DIR, "voice_config.json")
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "voice_config.json")

PIPER_PATH = resource_path("piper/piper.exe")
os.environ["ESPEAK_DATA_PATH"] = resource_path("espeak-ng-data")

TEST_TEXT = "Hello traveler. This is a voice test. How do I sound?"

pygame.mixer.init()


# -----------------------------
# CONFIG
# -----------------------------

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    if os.path.exists(DEFAULT_CONFIG_PATH):
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        save_config(cfg)
        return cfg

    return {"races": {}, "npc_overrides": {}}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


# -----------------------------
# CACHE
# -----------------------------

def clear_voice_cache():
    cache_dir = os.path.join(APPDATA_DIR, "voice_cache")

    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            try:
                os.remove(os.path.join(cache_dir, f))
            except:
                pass

    print("[CACHE] Cleared")


# -----------------------------
# MODEL RESOLVE (🔥 FIXED)
# -----------------------------

def resolve_model_path(model):

    if not model:
        return ""

    model = model.replace("\\", "/")

    # Always use AppData models folder
    if not os.path.isabs(model):
        model = os.path.join(APPDATA_DIR, "models", os.path.basename(model))

    model = os.path.normpath(model)

    return model


def get_fallback_model(race, gender):
    # Prioritize AppData models per race/gender
    appdata_models_dir = os.path.join(APPDATA_DIR, f"models/{race}/{gender}")
    
    if os.path.isdir(appdata_models_dir):
        files = [f for f in os.listdir(appdata_models_dir) if f.endswith(".onnx")]
        files.sort(key=lambda x: ("high" not in x.lower(), x))
        if files:
            return os.path.join(appdata_models_dir, files[0])
    
    # Fallback to AppData root
    appdata_root = os.path.join(APPDATA_DIR, "models")
    if os.path.isdir(appdata_root):
        files = [f for f in os.listdir(appdata_root) if f.endswith(".onnx")]
        files.sort(key=lambda x: ("high" not in x.lower(), x))
        if files:
            return os.path.join(appdata_root, files[0])

    # Fall back to bundle per race/gender
    bundle_models_dir = resource_path(f"models/{race}/{gender}")

    if os.path.isdir(bundle_models_dir):
        files = [f for f in os.listdir(bundle_models_dir) if f.endswith(".onnx")]
        files.sort(key=lambda x: ("high" not in x.lower(), x))
        if files:
            return os.path.join(bundle_models_dir, files[0])

    # Fall back to bundle root
    bundle_root = resource_path("models/root")
    if os.path.isdir(bundle_root):
        files = [f for f in os.listdir(bundle_root) if f.endswith(".onnx")]
        files.sort(key=lambda x: ("high" not in x.lower(), x))
        if files:
            return os.path.join(bundle_root, files[0])

    return ""


def get_effective_model(model, race, gender):

    model = resolve_model_path(model)

    if model and os.path.isfile(model):
        return model

    fallback = get_fallback_model(race, gender)

    if fallback:
        print(f"[MODEL] Using fallback: {fallback}")
        return fallback

    print("[ERROR] No model found")
    return ""


# -----------------------------
# SPEAKERS (JSON BASED)
# -----------------------------

def get_speakers_from_model(model_path):

    json_path = model_path + ".json"

    if not os.path.exists(json_path):
        print("[ERROR] No model JSON found")
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("speaker_id_map", {})

    except Exception as e:
        print("[ERROR] Failed to read speakers:", e)
        return {}


def load_speakers(model, listbox):

    listbox.delete(0, tk.END)

    if not model or not os.path.exists(model):
        print("[ERROR] Model not found")
        return

    speakers = get_speakers_from_model(model)

    if not speakers:
        print("[WARNING] No speakers found")
        return

    # Deduplicate by speaker id
    seen = set()
    for name, sid in speakers.items():
        if sid not in seen:
            listbox.insert(tk.END, f"{name} ({sid})")
            seen.add(sid)


# -----------------------------
# AUDIO
# -----------------------------

def play_audio(file):
    try:
        sound = pygame.mixer.Sound(file)
        sound.play()
    except Exception as e:
        print("[AUDIO ERROR]", e)


# -----------------------------
# GENERATE SAMPLE
# -----------------------------

def generate_sample(model, speaker, speed, noise):

    if not model or not os.path.exists(model):
        print("[ERROR] Model not found")
        return

    output = os.path.join(APPDATA_DIR, "sample.wav")

    # Convert UI speed to Piper's length-scale semantics
    # UI: lower => slower, higher => faster
    # Piper: length-scale >1 is faster, <1 is slower
    length_scale = 1.0 / speed if speed > 0 else 1.0
    
    # Extract speaker ID from format "name (123)" if needed
    speaker_id = None
    if speaker and "(" in speaker:
        try:
            speaker_id = int(speaker.split("(")[-1].rstrip(")"))
        except:
            speaker_id = None
    elif speaker:
        try:
            speaker_id = int(speaker)
        except:
            speaker_id = None
    
    # Debug logging
    print(f"[VOICE] Testing voice sample")
    print(f"[VOICE] Model: {model}")
    print(f"[VOICE] Speaker ID: {speaker_id if speaker_id is not None else 'default (0)'}")
    print(f"[VOICE] Speed (UI): {speed:.2f} → Length-scale: {length_scale:.3f}")
    print(f"[VOICE] Noise: {noise:.2f}")

    cmd = [
        PIPER_PATH,
        "--model", model,
        "--output_file", output,
        "--length-scale", str(length_scale),
        "--noise-scale", str(noise),
        "--noise-w", "0.75"
    ]

    if speaker_id is not None:
        cmd += ["--speaker", str(speaker_id)]

    subprocess.run(cmd, input=TEST_TEXT.encode("utf-8"))

    timeout = time.time() + 5

    while True:
        if os.path.exists(output) and os.path.getsize(output) > 1000:
            break
        if time.time() > timeout:
            print("[ERROR] Failed to generate audio")
            return
        time.sleep(0.05)

    play_audio(output)


# -----------------------------
# UI
# -----------------------------

def open_window():

    cfg = load_config()

    root = tk._default_root
    if root is None:
        root = tk.Tk()
        root.withdraw()

    win = tk.Toplevel(root)
    win.title("Voice Config")
    win.geometry("530x640")
    win.resizable(False, False)

    # -----------------------------
    # MAIN LAYOUT
    # -----------------------------
    main_frame = tk.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    left_frame = tk.Frame(main_frame)
    left_frame.grid(row=0, column=0, sticky="n")

    right_frame = tk.Frame(main_frame)
    right_frame.grid(row=0, column=1, padx=20)

    left_frame.grid_columnconfigure(0, weight=1)

    # -----------------------------
    # VARIABLES
    # -----------------------------
    race_var = tk.StringVar(value="human")
    gender_var = tk.StringVar(value="male")
    model_var = tk.StringVar()
    speaker_var = tk.StringVar()
    speed_var = tk.DoubleVar(value=1.0)
    noise_var = tk.DoubleVar(value=0.6)
    npc_name_var = tk.StringVar()

    # -----------------------------
    # HELPERS
    # -----------------------------
    def add_label(text):
        tk.Label(left_frame, text=text).grid(column=0, sticky="ew", pady=3)

    def add_widget(widget):
        widget.grid(column=0, sticky="ew")

    # -----------------------------
    # UI ELEMENTS (🔥 MUST BE HERE)
    # -----------------------------
    add_label("Race")
    race_dropdown = ttk.Combobox(left_frame, textvariable=race_var,
                                values=["human","elf","dwarf","wizard","hobbit"],
                                state="readonly")
    add_widget(race_dropdown)

    add_label("Gender")
    gender_dropdown = ttk.Combobox(left_frame, textvariable=gender_var,
                                  values=["male","female"],
                                  state="readonly")
    add_widget(gender_dropdown)

    add_label("Special Character Name")
    add_widget(tk.Entry(left_frame, textvariable=npc_name_var))

    add_label("Model Path")
    add_widget(tk.Entry(left_frame, textvariable=model_var))

    tk.Button(left_frame, text="Browse Model",
              command=lambda: model_var.set(
                  filedialog.askopenfilename(filetypes=[("ONNX", "*.onnx")])
              )).grid(column=0, pady=5, sticky="ew")

    add_label("Speaker ID")
    add_widget(tk.Entry(left_frame, textvariable=speaker_var))

    add_label("Speed")
    add_widget(tk.Scale(left_frame, from_=0.7, to=1.3, resolution=0.01,
                        orient="horizontal", variable=speed_var))

    add_label("Noise")
    add_widget(tk.Scale(left_frame, from_=0.3, to=1.0, resolution=0.01,
                        orient="horizontal", variable=noise_var))

    tk.Button(left_frame, text="▶ Test Voice",
              command=lambda: generate_sample(
                  get_effective_model(model_var.get(), race_var.get(), gender_var.get()),
                  speaker_var.get(),
                  speed_var.get(),
                  noise_var.get()
              )).grid(column=0, pady=10, sticky="ew")

    # -----------------------------
    # LOGIC
    # -----------------------------
    def on_npc_name_change(*args):
        name = npc_name_var.get().strip()

        if name:
            race_dropdown.config(state="disabled")
            gender_dropdown.config(state="disabled")
            model_var.set("models/en_US-libritts-high.onnx")
        else:
            race_dropdown.config(state="readonly")
            gender_dropdown.config(state="readonly")

    def load_selected_config(*args):
        if npc_name_var.get().strip():
            return

        race = race_var.get()
        gender = gender_var.get()

        data = cfg.get("races", {}).get(race, {}).get(gender, {})

        model_var.set(get_effective_model(data.get("model_path"), race, gender) or "")
        speaker_var.set(str(data.get("speaker_id", "")))

        emotion = data.get("emotion", {})
        speed_var.set(emotion.get("speed", 1.0))
        noise_var.set(emotion.get("noise", 0.6))

    # -----------------------------
    # SAVE
    # -----------------------------
    def save():
        race = race_var.get()
        gender = gender_var.get()
        npc_name = npc_name_var.get().strip().lower()

        if npc_name:
            cfg.setdefault("npc_overrides", {})[npc_name] = {
                "model_path": "models/en_US-libritts-high.onnx",
                "speaker_id": int(speaker_var.get()) if speaker_var.get() else -1,
                "emotion": {
                    "speed": speed_var.get(),
                    "noise": noise_var.get()
                }
            }

        cfg.setdefault("races", {}).setdefault(race, {})[gender] = {
            "use_custom_model": True,
            "model_path": model_var.get(),
            "use_speaker_id": True,
            "speaker_id": int(speaker_var.get()) if speaker_var.get() else -1,
            "emotion": {
                "speed": speed_var.get(),
                "noise": noise_var.get()
            }
        }

        save_config(cfg)
        clear_voice_cache()
        messagebox.showinfo("Saved", "Config saved!")

    tk.Button(left_frame, text="💾 SAVE CONFIG",
              bg="#4CAF50", fg="white",
              command=save).grid(column=0, pady=10, sticky="ew")

    # -----------------------------
    # RIGHT SIDE
    # -----------------------------
    tk.Label(right_frame, text="Available Speaker IDs").pack()

    list_frame = tk.Frame(right_frame)
    list_frame.pack()

    speaker_list = tk.Listbox(list_frame, width=30, height=25)
    speaker_list.pack(side="left")

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    speaker_list.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=speaker_list.yview)

    speaker_list.bind("<<ListboxSelect>>",
        lambda e: speaker_var.set(
            speaker_list.get(speaker_list.curselection()).split("(")[-1].replace(")", "")
        ) if speaker_list.curselection() else None
    )

    tk.Button(right_frame, text="Load Speakers",
              command=lambda: load_speakers(
                  get_effective_model(model_var.get(), race_var.get(), gender_var.get()),
                  speaker_list
              )).pack(pady=5)

    # -----------------------------
    # HOOKS (🔥 MUST BE LAST)
    # -----------------------------
    npc_name_var.trace_add("write", on_npc_name_change)
    race_var.trace_add("write", load_selected_config)
    gender_var.trace_add("write", load_selected_config)

    load_selected_config()

    # Remove duplicate UI and keep only one set of widgets
    # (already defined above)

    # (Removed duplicate speaker list and widgets)