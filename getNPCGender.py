import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def find_npc_in_the_file(search_string, encoding="utf-8"):
    file_path = resource_path("Resources/NPCs/npcs.txt")
    try:
        with open(file_path, "r", encoding=encoding) as file:
            for line in file:
                if search_string.lower() in line.lower():
                    return line
        return None
    except UnicodeDecodeError:
        print(f"[NPC Gender] Unable to decode the file using {encoding}.")
        return None
    except FileNotFoundError:
        print(f"[NPC Gender] File not found: {file_path}")
        return None

def return_npc_gender(search_string):
    result = find_npc_in_the_file(search_string)
    if result:
        lower = result.lower()
        if "[m]" in lower:
            return "male"
        elif "[f]" in lower:
            return "female"
    return "unknown"
