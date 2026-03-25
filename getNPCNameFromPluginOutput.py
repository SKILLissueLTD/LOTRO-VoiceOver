import os
from pathlib import Path
import getNPCGender

file_path = str(Path.home() / "Documents") + "/The Lord of the Rings Online/Script.log"


def get_npc_info():

    if not os.path.exists(file_path):
        print("[NPC Plugin] Script.log not found")
        return "unknown", "Narrator"

    try:

        with open(file_path, "r", encoding="utf-8") as file:

            lines = file.readlines()

            if not lines:
                return "unknown", "Narrator"

            last_line = lines[-1].strip()

            npc_name = last_line

            gender = getNPCGender.return_npc_gender(npc_name)

            return gender, npc_name

    except Exception as e:

        print(f"[NPC Plugin] Error reading Script.log: {e}")

        return "unknown", "Narrator"