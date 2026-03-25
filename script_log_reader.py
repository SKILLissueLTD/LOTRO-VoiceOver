import os
import time

class ScriptLogReader:
    def __init__(self, path):
        self.path = path
        self.last_size = 0

    def wait_for_file(self):
        print("[LOG] Waiting for Script.log...")
        while not os.path.exists(self.path):
            time.sleep(1)
        print("[LOG] Script.log found")

    def read_new_lines(self):
        try:
            current_size = os.path.getsize(self.path)

            if current_size < self.last_size:
                self.last_size = 0

            if current_size == self.last_size:
                return []

            with open(self.path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self.last_size)
                new_data = f.read()
                self.last_size = current_size

            lines = new_data.splitlines()
            lines = [l.strip() for l in lines if l.strip()]

            return lines

        except Exception as e:
            print("[LOG ERROR]", e)
            return []