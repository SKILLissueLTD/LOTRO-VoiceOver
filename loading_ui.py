import tkinter as tk
from tkinter import ttk
import queue
import time


class LoadingUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LOTRO Voiceover Setup")
        self.root.geometry("420x150")
        self.root.resizable(False, False)

        self.running = True

        self.label = tk.Label(self.root, text="Starting...", font=("Segoe UI", 10))
        self.label.pack(pady=(10, 5))

        self.progress = ttk.Progressbar(self.root, length=320, mode="determinate")
        self.progress.pack(pady=5)

        self.info = tk.Label(self.root, text="", font=("Segoe UI", 8))
        self.info.pack()

        # -----------------------------
        # INTERNAL STATE
        # -----------------------------
        self.current_progress = 0
        self.target_progress = 0
        self.start_time = None

        # thread-safe communication
        self.queue = queue.Queue()

        # start loops (MAIN THREAD ONLY)
        self.root.after(16, self.animate_progress)
        self.root.after(50, self.process_queue)

    # -----------------------------
    # MAIN LOOP (RUN IN MAIN THREAD)
    # -----------------------------
    def run(self):
        self.root.mainloop()

    # -----------------------------
    # QUEUE PROCESSING (SAFE)
    # -----------------------------
    def process_queue(self):
        if not self.running:
            return

        while not self.queue.empty():
            cmd, value = self.queue.get()

            if cmd == "text":
                self.label.config(text=value)

            elif cmd == "progress":
                self.target_progress = value

            elif cmd == "stats":
                self.info.config(text=value)

            elif cmd == "finish":
                self._finish_ui()

            elif cmd == "close":
                self.running = False
                self.root.destroy()
                return

        self.root.after(50, self.process_queue)

    # -----------------------------
    # THREAD-SAFE METHODS
    # -----------------------------
    def set_text(self, text):
        self.queue.put(("text", text))

    def set_progress(self, value):
        self.queue.put(("progress", value))

    def update_download_stats(self, downloaded, total):
        if total <= 0:
            return

        now = time.time()

        if self.start_time is None:
            self.start_time = now
            return

        elapsed = now - self.start_time
        speed = downloaded / elapsed if elapsed > 0 else 0

        remaining = total - downloaded
        eta = remaining / speed if speed > 0 else 0

        speed_mb = speed / (1024 * 1024)

        text = f"{speed_mb:.2f} MB/s  |  ETA: {int(eta)}s"
        self.queue.put(("stats", text))

    def finish(self):
        self.queue.put(("finish", None))

    def close(self):
        self.queue.put(("close", None))

    # -----------------------------
    # INTERNAL UI METHODS (MAIN THREAD ONLY)
    # -----------------------------
    def _finish_ui(self):
        self.target_progress = 100
        self.label.config(text="Setup complete ✓")
        self.info.config(text="")

        def safe_close():
            self.running = False
            self.root.destroy()

        self.root.after(1200, safe_close)

    # -----------------------------
    # SMOOTH ANIMATION (60 FPS)
    # -----------------------------
    def animate_progress(self):
        if not self.running:
            return

        if self.current_progress < self.target_progress:
            self.current_progress += (self.target_progress - self.current_progress) * 0.2

        self.progress["value"] = self.current_progress

        self.root.after(16, self.animate_progress)