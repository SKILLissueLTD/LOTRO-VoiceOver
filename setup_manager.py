import os
import urllib.request
import zipfile
import shutil

APPDATA = os.path.join(os.getenv("APPDATA"), "LOTROVoiceover")

FFMPEG_DIR = os.path.join(APPDATA, "ffmpeg")
MODELS_DIR = os.path.join(APPDATA, "models")

# ✅ Stable FFmpeg build
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# ✅ Piper model + config
MODEL_NAME = "en_US-libritts-high"
MODEL_URL = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts/high/{MODEL_NAME}.onnx?download=true"
MODEL_JSON_URL = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/libritts/high/{MODEL_NAME}.onnx.json?download=true"


# -----------------------------
# SETUP
# -----------------------------
def ensure_dirs():
    os.makedirs(APPDATA, exist_ok=True)
    os.makedirs(FFMPEG_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)


# -----------------------------
# CHECK IF SETUP NEEDED
# -----------------------------
def is_setup_required():
    ffmpeg_exe = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    model_path = os.path.join(MODELS_DIR, f"{MODEL_NAME}.onnx")

    return not (os.path.exists(ffmpeg_exe) and os.path.exists(model_path))


# -----------------------------
# FILE VALIDATION
# -----------------------------
def is_valid_file(path, min_size=10000):
    return os.path.exists(path) and os.path.getsize(path) > min_size


# -----------------------------
# DOWNLOAD HELPER (WITH SPEED + ETA)
# -----------------------------
def download_file(url, dest, progress_callback=None, stats_callback=None):
    tmp = dest + ".tmp"

    try:
        print(f"[DOWNLOAD] {url}")

        def reporthook(block_num, block_size, total_size):
            downloaded = block_num * block_size

            if total_size > 0:
                percent = min(downloaded * 100 / total_size, 100)

                if progress_callback:
                    progress_callback(percent)

                if stats_callback:
                    stats_callback(downloaded, total_size)

        urllib.request.urlretrieve(url, tmp, reporthook)

        os.replace(tmp, dest)

        if progress_callback:
            progress_callback(100)

        print(f"[DONE] {dest}")

    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)

        print(f"[ERROR] Failed to download: {url}")
        raise RuntimeError("Download failed.") from e


# -----------------------------
# FFMPEG
# -----------------------------
def ensure_ffmpeg(progress_callback=None, stats_callback=None):
    ensure_dirs()

    ffmpeg_exe = os.path.join(FFMPEG_DIR, "ffmpeg.exe")

    if is_valid_file(ffmpeg_exe, 100000):
        print("[SETUP] FFmpeg already installed")
        return ffmpeg_exe

    print("[SETUP] Installing FFmpeg...")

    zip_path = os.path.join(APPDATA, "ffmpeg.zip")

    download_file(
        FFMPEG_URL,
        zip_path,
        progress_callback,
        stats_callback
    )

    extract_dir = os.path.join(APPDATA, "ffmpeg_extract")

    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except Exception as e:
        raise RuntimeError("Failed to extract FFmpeg archive") from e
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

    found = False

    for root, dirs, files in os.walk(extract_dir):
        if "ffmpeg.exe" in files:
            src = os.path.join(root, "ffmpeg.exe")
            shutil.copy2(src, ffmpeg_exe)
            found = True
            break

    shutil.rmtree(extract_dir, ignore_errors=True)

    if not found or not is_valid_file(ffmpeg_exe, 100000):
        raise RuntimeError("FFmpeg installation failed")

    print("[SETUP] FFmpeg ready")
    return ffmpeg_exe


# -----------------------------
# MODEL
# -----------------------------
def ensure_model(progress_callback=None, stats_callback=None):
    ensure_dirs()

    model_path = os.path.join(MODELS_DIR, f"{MODEL_NAME}.onnx")
    json_path = model_path + ".json"

    need_model = not is_valid_file(model_path)
    need_json = not is_valid_file(json_path, 100)

    if need_model or need_json:
        print("[SETUP] Installing voice model...")

        if need_model:
            download_file(
                MODEL_URL,
                model_path,
                progress_callback,
                stats_callback
            )

        if need_json:
            download_file(
                MODEL_JSON_URL,
                json_path,
                progress_callback,
                stats_callback
            )

        print("[SETUP] Model ready")
    else:
        print("[SETUP] Model already installed")

    return {
        "model": model_path,
        "model_json": json_path
    }


# -----------------------------
# MAIN SETUP ENTRY (UI READY)
# -----------------------------
def run_setup(progress_callback=None, status_callback=None, stats_callback=None):

    def update_status(text):
        print(text)
        if status_callback:
            status_callback(text)

    # -----------------------------
    # STEP 1 — FFMPEG
    # -----------------------------
    update_status("Installing FFmpeg...")
    ffmpeg_path = ensure_ffmpeg(progress_callback, stats_callback)

    if progress_callback:
        progress_callback(0)

    # -----------------------------
    # STEP 2 — MODEL
    # -----------------------------
    update_status("Installing voice model...")
    model_info = ensure_model(progress_callback, stats_callback)

    # -----------------------------
    # DONE
    # -----------------------------
    update_status("Setup complete!")

    return {
        "ffmpeg": ffmpeg_path,
        "model": model_info["model"],
        "model_json": model_info["model_json"]
    }