from utils import resource_path
import globalVariables
import pytesseract
from PIL import Image
import lookForTesseract
import cleanText
import re
import cv2
import numpy as np
import time
from difflib import SequenceMatcher

from piperTTSEngine import get_quest_box_region


# -----------------------------
# Scan control
# -----------------------------

last_scan_time = 0
SCAN_COOLDOWN = 1.0

quest_window_open = False


# -----------------------------
# Normalize OCR text
# -----------------------------

def normalize_text(t):

    t = t.lower()
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[^a-z0-9 ]', '', t)

    return t.strip()


# -----------------------------
# Text similarity
# -----------------------------

def text_similarity(a, b):

    if not a or not b:
        return 0

    a = normalize_text(a)
    b = normalize_text(b)

    return SequenceMatcher(None, a, b).ratio()


# -----------------------------
# OCR error correction (SAFE)
# -----------------------------

def fix_common_ocr_errors(text):

    text = text.replace("1", "I")

    text = re.sub(r"\bTam\b", "I am", text)
    text = re.sub(r"\bLam\b", "I am", text)
    text = re.sub(r"\bIam\b", "I am", text)
    text = re.sub(r"\bIarn\b", "I am", text)

    text = re.sub(r"\bl\b", "I", text)

    text = re.sub(r"'\s*T\b", "'I", text)

    text = re.sub(r"(^|\.\s+)T\s", r"\1I ", text)

    # OCR noise
    text = re.sub(r'\bss([a-z]+)', r's\1', text)
    text = re.sub(r'\baa([a-z]+)', r'a\1', text)

    fixes = {
        "wilI": "will",
        "alI": "all",
        "aanymore": "anymore",
        "sspring": "spring",
        "sspringtime": "springtime",
        "ny more": "anymore",
        "dont": "don't",
        "cant": "can't",
        "omehow": "somehow",
        "ertain": "certain",
        "pring": "spring",
    }

    for wrong, correct in fixes.items():
        text = text.replace(wrong, correct)

    return text


# -----------------------------
#  STRONG UI TEXT REMOVAL
# -----------------------------

def remove_lotro_ui_text(text):

    # CUT EVERYTHING AFTER THESE
    cut_patterns = [
        r'This is a repeatable quest',
        r'that you have previously completed',
        r'You have completed',
    ]

    for pattern in cut_patterns:
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        text = parts[0]

    # Remove other UI junk
    cleanup_patterns = [
        r'Rewards:.*',
        r'Click .* to continue.*',
        r'Quest Completed.*'
    ]

    for p in cleanup_patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE | re.DOTALL)

    return text.strip()


# -----------------------------
# Clean dialogue
# -----------------------------

from advanced_spellcheck import fix_text_advanced

def clean_dialogue(text):

    text = fix_common_ocr_errors(text)

    # SMART SYSTEM
    text = fix_text_advanced(text)

    text = remove_lotro_ui_text(text)

    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# -----------------------------
# Format dialogue
# -----------------------------

def format_dialogue(text):

    sentences = re.split(r'(?<=[.!?])\s+', text)

    cleaned = []

    for s in sentences:
        s = s.strip()
        if len(s) > 2:
            cleaned.append(s)

    return "\n\n".join(cleaned)


# -----------------------------
# OCR detection
# -----------------------------

def ocr_detection_and_cleaup():

    global last_scan_time
    global quest_window_open

    now = time.time()

    if now - last_scan_time < SCAN_COOLDOWN:
        return False

    last_scan_time = now


    # -----------------------------
    # Detect quest window
    # -----------------------------

    body_img, title_img = get_quest_box_region()


    # -----------------------------
    # Dialogue closed
    # -----------------------------

    if body_img is None:

        if quest_window_open:
            print("[OCR] Quest window closed")

        quest_window_open = False

        globalVariables.text_ocr = ""
        globalVariables.title_ocr = ""

        return False


    # -----------------------------
    # Dialogue still open
    # DO NOT re-read
    # -----------------------------

    if quest_window_open:
        return False


    # Dialogue just opened
    quest_window_open = True

    print("[OCR] Quest window detected")


    # -----------------------------
    # Title OCR
    # -----------------------------

    if title_img is not None and title_img.size > 0:

        gray_title = cv2.cvtColor(title_img, cv2.COLOR_BGR2GRAY)

        _, thresh_title = cv2.threshold(
            gray_title,
            100,
            255,
            cv2.THRESH_BINARY_INV
        )

        raw_title = pytesseract.image_to_string(
            thresh_title,
            config='--psm 7'
        )

        globalVariables.title_ocr = raw_title.strip()

    else:
        globalVariables.title_ocr = ""


    # -----------------------------
    # Body OCR
    # -----------------------------

    quest_pil = Image.fromarray(body_img)

    globalVariables.tesseract_language = (
        lookForTesseract.load_tesseract_lang() or "eng"
    )

    raw_text = pytesseract.image_to_string(
        quest_pil,
        lang=globalVariables.tesseract_language
    )

    cleaned = cleanText.clear(raw_text)

    cleaned = clean_dialogue(cleaned)

    final_text = format_dialogue(cleaned)


    # Safety check
    if len(final_text) < 10:
        return False


    globalVariables.text_ocr = final_text
    globalVariables.already_talked = False

    print("[OCR] New quest dialogue captured")

    return True