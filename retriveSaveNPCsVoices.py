import json
import os
import globalVariables

file_path = os.path.join(globalVariables.config_path, "npcs_voices.json")


def create_npcs_voices_file():
    os.makedirs(globalVariables.config_path, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            json.dump([], file)


def read_npc_data():
    create_npcs_voices_file()
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            return []
    except json.JSONDecodeError:
        print("[NPC Voices] JSON corrupted. Reinitializing.")
        with open(file_path, "w") as file:
            json.dump([], file)
        return []
    except Exception as e:
        print(f"[NPC Voices] Failed to read JSON: {e}")
        return []


def write_npc_data(data):
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"[NPC Voices] Failed to write JSON: {e}")


def normalize_name(name):
    return name.strip().lower()


def get_voice_by_name(name):
    name = normalize_name(name)
    for item in read_npc_data():
        if normalize_name(item.get("Name", "")) == name:
            return item.get("Voice", "")
    return ""


def get_info_by_name(name):
    name = normalize_name(name)
    for item in read_npc_data():
        if normalize_name(item.get("Name", "")) == name:
            return item
    return None


def add_info_to_json(new_data):
    data = read_npc_data()
    new_name = normalize_name(new_data.get("Name", ""))

    for i, item in enumerate(data):
        if normalize_name(item.get("Name", "")) == new_name:
            data[i] = new_data  # Replace existing
            break
    else:
        data.append(new_data)  # Add new

    write_npc_data(data)
    print(f"[NPC Voices] Saved: {new_data}")
