from utils import resource_path
import os
import pygame
import time
import threading
import queue
import numpy as np
import cv2
import mss
import pytesseract
from difflib import SequenceMatcher

import globalVariables
from quest_popup import popup
from voices import speak
import getNPCNameFromPluginOutput


# -----------------------------
# Globals
# -----------------------------

audio_queue = queue.Queue()
playback_thread_started = False
paused = False

COOLDOWN_SECONDS = 60
DETECTED_SCALE = None


# -----------------------------
# Utils
# -----------------------------

def debug(msg):
    if globalVariables.debug_mode:
        print(msg)


def is_similar(a, b, threshold=0.5):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold


# -----------------------------
# AUDIO CONTROL
# -----------------------------

def stop_audio():

    pygame.mixer.stop()

    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
            audio_queue.task_done()
        except:
            break

    debug("[Audio] Force stopped")


def toggle_audio_pause():

    global paused
    paused = not paused

    print(f"[Audio] {'Paused' if paused else 'Resumed'}")


# -----------------------------
# AUDIO WORKER
# -----------------------------

def audio_playback_worker():

    pygame.mixer.init()

    while True:

        text = audio_queue.get()

        try:

            while paused:
                time.sleep(0.1)

            debug("[Audio] Playing line")

            try:
                popup.update_text(text)
                popup.show()
            except:
                pass

            time.sleep(0.1)

            gender, npc_name = getNPCNameFromPluginOutput.get_npc_info()

            if not npc_name:
                npc_name = "Narrator"

            debug(f"[TTS] NPC: {npc_name}")
            debug(f"[TTS] Gender: {gender}")

            speak(text, npc_name)

            while pygame.mixer.get_busy():

                if paused:
                    pygame.mixer.pause()
                else:
                    pygame.mixer.unpause()

                time.sleep(0.05)

            if audio_queue.empty():
                try:
                    popup.hide()
                except:
                    pass

        except Exception as e:
            print("[Audio Error]", e)

        finally:
            audio_queue.task_done()


def start_audio_playback_thread():

    global playback_thread_started

    if not playback_thread_started:
        threading.Thread(target=audio_playback_worker, daemon=True).start()
        playback_thread_started = True


start_audio_playback_thread()


# -----------------------------
# QUEST WINDOW DETECTION
# -----------------------------

def get_quest_box_region():

    global DETECTED_SCALE

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screen = np.array(sct.grab(monitor))[:, :, :3]

    h, w = screen.shape[:2]

    search = screen[int(h*0.15):int(h*0.85), int(w*0.15):int(w*0.85)]

    def safe_imread(path):
        p = resource_path(path)
        if not os.path.exists(p):
            p = path
        return cv2.imread(p)

    top_template = safe_imread("assets/quest_topcorner_template.png")
    bottom_template = safe_imread("assets/quest_bottomcorner_template.png")

    if top_template is None or bottom_template is None:
        print("[FATAL] TEMPLATE NOT FOUND")
        return None, None

    if DETECTED_SCALE is not None and not globalVariables.scan_ui_scale:
        scales = [DETECTED_SCALE]
    else:
        scales = np.linspace(0.7, 2.2, 20)

    best_top = best_bottom = None
    best_top_score = best_bottom_score = 0
    best_template = None
    best_scale = None

    for scale in scales:

        t_top = cv2.resize(top_template, None, fx=scale, fy=scale)
        t_bot = cv2.resize(bottom_template, None, fx=scale, fy=scale)

        if t_top.shape[0] >= search.shape[0]:
            continue

        res_top = cv2.matchTemplate(search, t_top, cv2.TM_CCOEFF_NORMED)
        _, v_top, _, loc_top = cv2.minMaxLoc(res_top)

        res_bot = cv2.matchTemplate(search, t_bot, cv2.TM_CCOEFF_NORMED)
        _, v_bot, _, loc_bot = cv2.minMaxLoc(res_bot)

        if v_top > best_top_score:
            best_top_score = v_top
            best_top = loc_top
            best_scale = scale

        if v_bot > best_bottom_score:
            best_bottom_score = v_bot
            best_bottom = loc_bot
            best_template = t_bot
            best_scale = scale

    if best_top_score < 0.82 or best_bottom_score < 0.82:
        debug("[OCR] Window not detected")
        return None, None

    if best_scale is not None:
        DETECTED_SCALE = best_scale
        debug(f"[OCR] UI Scale detected: {DETECTED_SCALE:.2f}")
        
        # Save scale to file for persistence
        appdata_dir = os.path.join(os.getenv("APPDATA"), "LOTROVoiceover")
        os.makedirs(appdata_dir, exist_ok=True)
        scale_file = os.path.join(appdata_dir, "ui_scale.txt")
        try:
            with open(scale_file, "w") as f:
                f.write(str(DETECTED_SCALE))
            debug(f"[OCR] UI Scale saved to {scale_file}")
        except:
            pass
        
        # Auto-disable scanning once scale is found
        globalVariables.scan_ui_scale = False
        debug("[OCR] Scanning disabled (scale found)")

    x_offset = int(w*0.15)
    y_offset = int(h*0.15)

    x1, y1 = best_top
    x2, y2 = best_bottom

    x1 += x_offset
    y1 += y_offset
    x2 += x_offset
    y2 += y_offset

    tw, th = best_template.shape[1], best_template.shape[0]

    body = screen[
        y1+50:y2+th-3,
        x1+3:x2+tw-45
    ]

    return body, None


# -----------------------------
# MAIN TTS ENTRY
# -----------------------------

async def tts_engine(text=None):

    if text is None:
        text = globalVariables.text_ocr.strip()

    if not text:
        return

    title = globalVariables.title_ocr.strip()

    globalVariables.is_book_quest = (
        "book" in title.lower() or "chapter" in title.lower()
    )

    if globalVariables.only_narrate_book_quests and not globalVariables.is_book_quest:
        return

    now = time.time()

    globalVariables.recent_lines = [
        x for x in globalVariables.recent_lines
        if now - x["time"] <= COOLDOWN_SECONDS
    ]

    for entry in globalVariables.recent_lines:
        if is_similar(text, entry["text"]):
            debug("[TTS] Skipping duplicate")
            return

    globalVariables.recent_lines.append({
        "text": text,
        "time": now
    })

    debug("[TTS] Queued")

    audio_queue.put(text)

    globalVariables.already_talked = True