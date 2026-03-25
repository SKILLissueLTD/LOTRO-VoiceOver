# This file exists to clean the most common misreads from Tesseract due to the LOTRO font
# and to apply basic grammar and phrasing corrections.

import re
import os
import globalVariables
#import language_tool_python
import sys
import tqdm

# Prevent crash by setting default output for tqdm to stdout
try:
    if tqdm.tqdm.__init__.__defaults__:
        tqdm.tqdm.__init__.__defaults__ = (*tqdm.tqdm.__init__.__defaults__[:-1], sys.stdout)
except Exception:
    pass  # Silently ignore if it fails, safe fallback




#tool = language_tool_python.LanguageTool('en-US')


def clear(text):
    # Step 1: Apply string replacements
    text = replace_strings(text)

    # Step 2: Normalize line spacing, preserve breaks
    cleaned_lines = []
    for line in text.splitlines():
        line = re.sub(r'\s+', ' ', line).strip()
        cleaned_lines.append(line)

    cleaned_text = '\n'.join(cleaned_lines)

    # Step 3: Remove invalid characters, preserving breaks
    allowed_chars = r'[^a-zA-Z0-9!?.;,:\-\'\"‘’“”äöüßàâçéèêëîïôûùÿæœÀÂÇÉÈÊËÎÏÔÛÙÜŸÆŒ \n]'
    cleaned_text = re.sub(allowed_chars, '', cleaned_text)

    # Step 4: Basic grammar and phrasing correction (skipping fantasy terms or short lines)
    corrected_lines = []
    for line in cleaned_text.splitlines():
        words = line.split()
        if len(words) < 5 or re.match(r'^[A-Z][a-z]+(?:[\s\-][A-Z][a-z]+)*$', line):
            corrected_lines.append(line.strip())  # skip correction
        else:
            corrected_lines.append(line.strip())

    return '\n'.join(corrected_lines).strip()


def create_replace_string_file():
    if not os.path.exists(globalVariables.config_path):
        os.makedirs(globalVariables.config_path)

    try:
        with open(os.path.join(globalVariables.config_path, "replace_string.txt"), "x", encoding='utf-8') as file:
            pass
    except FileExistsError:
        pass


def replace_strings(input_string):
    create_replace_string_file()

    file_path = os.path.join(globalVariables.config_path, "replace_string.txt")

    replacements = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 2:
                old_str, new_str = parts
                if new_str == '""':
                    new_str = ''
                replacements[old_str] = new_str

    for old_str, new_str in replacements.items():
        input_string = input_string.replace(old_str, new_str)

    return input_string
