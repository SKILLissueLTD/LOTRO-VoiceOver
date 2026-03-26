import sys
from tkinter import messagebox
import os
import pytesseract

import globalVariables

app_data_path = fr'C:\Users\{os.getlogin()}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

program_files_path = fr'C:\Program Files\Tesseract-OCR\tesseract.exe'


def create_tesseract_path_file():
    if not os.path.exists(globalVariables.config_path):
        os.makedirs(globalVariables.config_path)

    try:
        with open(globalVariables.config_path + r"/tesseract_path.txt", "x") as file:
            pass
    except FileExistsError:
        pass


def create_tesseract_lang_file():
    if not os.path.exists(globalVariables.config_path):
        os.makedirs(globalVariables.config_path)

    try:
        with open(globalVariables.config_path + r"/tesseract_lang.txt", "x") as file:
            pass
    except FileExistsError:
        pass


def load_tesseract_lang():
    path = globalVariables.config_path
    lang = ""

    try:
        with open(path + "/tesseract_lang.txt", "r") as file:
            lines = file.readlines()

            if len(lines) > 0:
                lang = lines[0].strip()

            return lang
    except FileNotFoundError:
        return "ops"


def load_tesseract_path():
    path = globalVariables.config_path

    try:
        with open("tesseract_path.txt", "r") as file:
            lines = file.readlines()

            if len(lines) > 0:
                path = lines[0].strip()

            return path
    except FileNotFoundError:
        return ""


def look_for_tesseract():
    import shutil

    appdata = os.path.join(os.getenv("APPDATA"), "LOTROVoiceover")
    config_path = os.path.join(appdata, "tesseract_path.txt")

    # -----------------------------
    # 1. SAVED PATH
    # -----------------------------
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                path = f.read().strip()

            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"[TESSERACT] Using saved: {path}")
                return path
        except:
            pass

    # -----------------------------
    # 2. BUNDLED (EXE SAFE)
    # -----------------------------
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    bundled = os.path.join(base_path, "tesseract", "tesseract.exe")

    if os.path.exists(bundled):
        pytesseract.pytesseract.tesseract_cmd = bundled
        print(f"[TESSERACT] Using bundled: {bundled}")

        os.makedirs(appdata, exist_ok=True)
        with open(config_path, "w") as f:
            f.write(bundled)

        return bundled

    # -----------------------------
    # 3. SYSTEM PATH
    # -----------------------------
    system_path = shutil.which("tesseract")

    if system_path:
        pytesseract.pytesseract.tesseract_cmd = system_path
        print(f"[TESSERACT] Using system: {system_path}")

        os.makedirs(appdata, exist_ok=True)
        with open(config_path, "w") as f:
            f.write(system_path)

        return system_path

    # -----------------------------
    # ❌ FAIL
    # -----------------------------
    print("[TESSERACT] NOT FOUND")

    try:
        messagebox.showerror(
            "Missing Dependency",
            "Tesseract OCR not found.\nPlease reinstall the app."
        )
    except:
        pass

    return None
