import os
import re
import shutil
from symspellpy import SymSpell, Verbosity
from rapidfuzz import fuzz
from utils import resource_path


# -----------------------------
# DICTIONARY PATH
# -----------------------------
def get_dictionary_path():

    appdata_path = os.path.join(
        os.getenv("APPDATA"),
        "LOTROVoiceover",
        "symspell_dictionary.txt"
    )

    # 1. Already exists
    if os.path.exists(appdata_path):
        return appdata_path

    # 2. Bundled (EXE)
    bundled = resource_path("resources/symspell_dictionary.txt")
    if os.path.exists(bundled):
        os.makedirs(os.path.dirname(appdata_path), exist_ok=True)
        shutil.copy2(bundled, appdata_path)
        print("[SPELL] Copied dictionary from bundle")
        return appdata_path

    # 3. Dev fallback
    try:
        import symspellpy
        package_path = os.path.dirname(symspellpy.__file__)
        src = os.path.join(package_path, "frequency_dictionary_en_82_765.txt")

        if os.path.exists(src):
            os.makedirs(os.path.dirname(appdata_path), exist_ok=True)
            shutil.copy2(src, appdata_path)
            print("[SPELL] Extracted dictionary to AppData")
            return appdata_path

    except Exception as e:
        print("[SPELL] Failed to extract dictionary:", e)

    return None


# -----------------------------
# CLEAN DICTIONARY (FIX WARNING)
# -----------------------------
def clean_dictionary_file(path):

    cleaned_lines = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parts = line.strip().split()

            # must be exactly: word + number
            if len(parts) != 2:
                continue

            word, freq = parts

            if not freq.isdigit():
                continue

            cleaned_lines.append(f"{word} {freq}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print("[SPELL] Dictionary cleaned")


# -----------------------------
# LOAD NPC NAMES
# -----------------------------
NPC_FILES = [
    resource_path("Helpful Stuffs/NPCs/npcsEN.txt"),
    resource_path("Helpful Stuffs/NPCs/npcsFR.txt"),
    resource_path("Helpful Stuffs/NPCs/npcsDE.txt"),
]

protected_names = set()


def normalize_name(name):
    return re.sub(r'[^a-z]', '', name.lower())


def load_npc_names():
    for path in NPC_FILES:
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "[" not in line:
                    continue

                name = line.split("[", 1)[0].strip()

                for part in name.split():
                    protected_names.add(normalize_name(part))

    print(f"[SPELL] Loaded {len(protected_names)} protected names")


load_npc_names()


# -----------------------------
# INIT SPELL
# -----------------------------
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

dictionary_path = get_dictionary_path()

if dictionary_path:

    print("[SPELL] Using dictionary:", dictionary_path)

    # CLEAN FILE BEFORE LOADING
    clean_dictionary_file(dictionary_path)

    loaded = sym_spell.load_dictionary(dictionary_path, 0, 1, encoding="utf-8")

    if loaded:
        print("[SPELL] Dictionary loaded")
    else:
        print("[SPELL] Dictionary failed to load")

else:
    print("[SPELL] Dictionary NOT found (spell disabled)")


# -----------------------------
# TAG HANDLING (KEEP [m][f])
# -----------------------------
def split_tag(word):
    match = re.match(r"^(.+?)(\[[^\]]+\])$", word)
    if match:
        return match.group(1), match.group(2)
    return word, ""


# -----------------------------
# NAME DETECTION
# -----------------------------
def is_probably_name(word):

    base, _ = split_tag(word)

    if len(base) <= 2:
        return True

    norm = normalize_name(base)

    if norm in protected_names:
        return True

    if base and base[0].isupper():
        return True

    return False


# -----------------------------
# OCR ERROR DETECTION
# -----------------------------
def looks_like_ocr_error(word):

    if re.search(r"(.)\1{2,}", word):
        return True

    if re.search(r"[0-9]", word):
        return True

    if re.search(r"[a-z][A-Z]", word):
        return True

    return False


# -----------------------------
# SAFE CORRECTION
# -----------------------------
def correct_word(word):

    base, tag = split_tag(word)

    if not base.isalpha():
        return word

    if is_probably_name(word):
        return word

    suggestions = sym_spell.lookup(
        base.lower(),
        Verbosity.CLOSEST,
        max_edit_distance=2
    )

    if not suggestions:
        return word

    best = suggestions[0].term

    similarity = fuzz.ratio(base.lower(), best)

    if similarity < 80:
        return word

    return best + tag


# -----------------------------
# MAIN FIX
# -----------------------------
def fix_text_advanced(text):

    words = text.split()
    result = []

    for w in words:

        prefix = re.match(r"^\W+", w)
        suffix = re.match(r".*?(\W+)$", w)

        core = re.sub(r"^\W+|\W+$", "", w)

        if not core:
            result.append(w)
            continue

        if looks_like_ocr_error(core) or core.islower():
            fixed = correct_word(core)
        else:
            fixed = core

        if prefix:
            fixed = prefix.group() + fixed
        if suffix:
            fixed = fixed + suffix.group(1)

        result.append(fixed)

    return " ".join(result)