from symspellpy import SymSpell, Verbosity
import pkg_resources
import re

# -----------------------------
# INIT
# -----------------------------

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt"
)

sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

def fix_text_advanced(text):
    return text
# -----------------------------
# PROTECT NAMES (CRITICAL)
# -----------------------------

def is_probably_name(word):

    if len(word) > 3 and re.search(r"(ae|ia|el|th|nd|ir|iel)", word.lower()):
        return True

    # Capitalized mid-sentence → likely name
    if word[0].isupper():
        return True

    return False


# -----------------------------
# SAFE SPELL FIX
# -----------------------------

def fix_spelling_safe(text):

    words = text.split()
    corrected = []

    for w in words:

        # Skip names
        if is_probably_name(w):
            corrected.append(w)
            continue

        # Only fix lowercase normal words
        if not w.isalpha():
            corrected.append(w)
            continue

        suggestions = sym_spell.lookup(
            w.lower(),
            Verbosity.CLOSEST,
            max_edit_distance=1
        )

        if suggestions:
            best = suggestions[0].term

            # 🔥 ONLY fix if very similar (avoid wrong changes)
            if len(w) > 4:
                corrected.append(best)
            else:
                corrected.append(w)
        else:
            corrected.append(w)

    return " ".join(corrected)