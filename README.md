# 🎙️ LOTRO-VoiceOver

AI-powered real-time voice narration for *The Lord of the Rings Online*.  
Brings NPC dialogue to life using local text-to-speech with intelligent character detection.

---

## ✨ Features

- 🎧 Real-time voice narration for quests and dialogue  
- 🧠 Smart NPC detection (race, gender, special characters)  
- 🎚️ Per-race & per-character voice customization  
- 📏 Automatic UI scale detection  
- 🔊 Local AI TTS (Piper)  
- ⚡ Audio caching for smooth performance  
- 🧹 OCR cleanup + name protection  
- 🔄 Built-in updater for models and features  

---

## 🎮 How It Works

1. Detects quest/dialogue text from the game  
2. Cleans and corrects OCR errors  
3. Identifies NPC (race, gender, or custom override)  
4. Generates voice using local AI  
5. Plays it instantly in-game  

---

## ⚙️ Installation (Portable – No Setup Required)

1. Download the latest release  
2. Extract the folder  
3. Run: `LOTRO_Voiceover.exe`  

👉 No installation required. Fully portable.

---

## 🚀 First Launch Behavior

On first run, the app will automatically:

- Download FFmpeg  
- Download required Piper voice model  
- Initialize folders and configuration  
- Detect UI scale  

👉 No manual setup needed.

All data is stored in:
\Users<YOU>\AppData\Roaming\LOTROVoiceover

Includes:
- Models  
- Voice configuration  
- Dictionary  
- Voice cache  

---

## ⚡ Performance & Caching

- Generated voice lines are cached  
- Repeated dialogue plays instantly  
- Reduces CPU usage over time  

---

## 📂 Config & Data Access

You can open the config folder anytime via the tray menu:

👉 Right-click tray icon → **Open Config Folder**

---

## ⚠️ UI Compatibility

Currently, the plugin works reliably with the **original LOTRO UI skin**.

👉 Support for custom UI skins will be added in future updates.

---

## ⚠️ Required Plugin (Important)

This project requires the **getNPCName plugin**.

- It is bundled automatically  
- The app copies it to your LOTRO Plugins folder  

👉 You must enable it in the LOTRO character selection screen  

Without it, NPC detection will not work correctly.

---

## 🧪 Voice Configuration

Use the built-in Voice Config UI to:

- Assign voices per race  
- Adjust speed, noise, and tone  
- Add special characters (e.g. Gandalf, Bombadil)  

👉 Special characters override race detection automatically  

---

## 🧠 Custom NPC Voices

To assign a unique voice to a character:

1. Enter the name in **Special Character Name**  
2. Configure voice settings  
3. Click **Save**

---

## 🔄 Updater

The application includes an updater that:

- Notifies about new versions  
- Automatic downloading/updating is coming in future updates  
- Keeps configs and models safe  

---

## ⚠️ Notes

- First run may take a few seconds  
- Performance improves after caching  
- OCR is not perfect but heavily optimized  
- Audio quality and voices will improve over time  

---

## 🛠️ Tech Stack

- Piper TTS (local voice generation)  
- FFmpeg (audio processing)  
- pygame (audio playback)  
- SymSpell (text correction)  
- RapidFuzz (text matching)  
- pytesseract (OCR detection)  
- Python + PyInstaller  

---

## ❤️ Credits

- Original LOTROToSpeech project: https://github.com/ils94/LOTROToSpeech  
- Continued development by moveit124: https://github.com/moveit124/LOTROtoSpeech-moveit  
- NPC detection plugin (getNPCName / NPCGender system)  
- Piper TTS voices: https://github.com/rhasspy/piper  
- FFmpeg: https://ffmpeg.org/  
- Open-source libraries:
  - pygame  
  - SymSpell  
  - RapidFuzz  
  - pytesseract  
  - Python ecosystem contributors  

---

## 🚀 Future Plans

- Improved audio quality and voice naturalness  
- Support for custom LOTRO UI skins  
- Better NPC recognition and edge-case handling  
- More voice models  
- Fully automatic updater (download + install)  
- UI and usability improvements  

---

## 📜 License

MIT License
