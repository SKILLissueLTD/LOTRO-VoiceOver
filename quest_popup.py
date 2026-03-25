from utils import resource_path
import tkinter as tk
import threading
import json
import os
import globalVariables

SETTINGS_FILE = "popup_settings.json"

class QuestPopup:
    def __init__(self):
        self.text = ""
        self.popup_enabled = False
        self.load_settings()

        self.thread = threading.Thread(target=self._run_window, daemon=True)
        self.thread.start()

    def _run_window(self):
        try:
            self.root = tk.Tk()
            self.root.title("Quest Text")
            self.root.attributes("-topmost", True)
            self.root.overrideredirect(True)
            self.root.configure(bg="#111111")
            self.root.withdraw()  # Always start hidden

            self.label = tk.Label(
                self.root,
                text=self.text,
                font=("Arial", 10),
                fg="white",
                bg="#111111",
                justify="left",
                wraplength=300
            )
            self.label.pack(padx=10, pady=10)
            self.root.after(0, self._position_window)
            self.root.mainloop()
        except Exception as e:
            print(f"[Popup CRASH] _run_window failed: {e}")

    def _position_window(self):
        try:
            self.root.update_idletasks()
            self.label.update_idletasks()

            width = max(self.label.winfo_reqwidth() + 20, 300)
            height = max(self.label.winfo_reqheight() + 20, 100)

            print(f"[Popup DEBUG] Positioning window: width={width}, height={height}")

            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - width - 20
            y = screen_height - height - 60
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            print(f"[Popup Error] _position_window failed: {e}")

    def update_text(self, new_text):
        self.text = new_text
        if hasattr(self, "label") and self.popup_enabled:
            def do_update():
                print("[Popup DEBUG] Updating popup with text:")
                print(repr(new_text))

                self.label.config(text=new_text)
                self.label.update_idletasks()
                print(f"[Popup DEBUG] Label width: {self.label.winfo_reqwidth()} | height: {self.label.winfo_reqheight()}")
                self._position_window()
            self.root.after(0, do_update)

    def toggle_popup(self):
        self.popup_enabled = not self.popup_enabled
        self.save_settings()

        if self.popup_enabled:
            self.show_popup()
        else:
            self.hide_popup()

    def hide(self):
        if hasattr(self, "root"):
            self.root.withdraw()

    def show(self):
        if self.popup_enabled and hasattr(self, "root"):
            self.root.deiconify()

    def save_settings(self):
        try:
            data = {
                "popup_enabled": self.popup_enabled,
                "only_narrate_book_quests": globalVariables.only_narrate_book_quests,
                "use_edge_tts": globalVariables.use_edge_tts
            }
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[Settings Error] Could not save settings: {e}")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.popup_enabled = data.get("popup_enabled", False)

                    # Load global toggles here
                    globalVariables.only_narrate_book_quests = data.get("only_narrate_book_quests", False)
                    globalVariables.use_edge_tts = data.get("use_edge_tts", True)

            except Exception as e:
                print(f"[Settings Error] Could not load settings: {e}")


popup = QuestPopup()
