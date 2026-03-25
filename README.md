# 🎙️ LOTRO-VoiceOver

AI-powered real-time voice narration for *The Lord of the Rings Online*.  
Brings NPC dialogue to life using local text-to-speech with intelligent character detection.

---

## ✨ Features

- 🎧 Real-time voice narration for quests and dialogue  
- 🧠 Smart NPC detection (race, gender, special characters)  
- 🎚️ Per-race & per-character voice customization  
- 📏 Automatic UI scale detection (works on any UI setup)  
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

## ⚙️ Installation

1. Download the latest release  
2. Extract the folder  
3. Run: LOTRO_Voiceover.exe


### First launch will:
- Detect UI scale automatically  
- Create required folders  
- Initialize models  

---

## ⚠️ Required Plugin (Important)

This project requires the **getNPCName plugin**.

- It is automatically bundled with LOTRO-VoiceOver  
- The app will attempt to copy it to your LOTRO Plugins folder  

👉 You must ensure it is enabled in the LOTRO character selection screen

Without it, NPC name detection will not work correctly.

---

## 🧪 Voice Configuration

Use the built-in Voice Config UI to:

- Assign voices per race (human, elf, dwarf, etc.)  
- Set speaker ID, speed, and noise  
- Add special characters (e.g. Gandalf, Bombadil)  

👉 Special characters override race detection automatically  

---

## 🧠 Custom NPC Voices

To assign a unique voice to a character:

1. Enter the name in **Special Character Name**  
2. Configure voice settings  
3. Click **Save**  

The system will use that voice whenever the NPC appears.

---

## 🗂️ File Locations

All config and data are stored in:
C:\Users<YOU>\AppData\Roaming\LOTROVoiceover


Includes:
- voice_config.json  
- models/  
- voice_cache/  

---

## 🔄 Updater

The application includes an updater that:

- Downloads new models  
- Applies improvements  
- Keeps everything up to date  

---

## ⚠️ Notes

- First run may take a few seconds  
- Performance improves after caching  
- OCR is not perfect but heavily optimized  

---

## 🛠️ Tech Stack

- Piper TTS (local voice generation)  
- pygame (audio playback)  
- SymSpell (text correction)  
- RapidFuzz (matching)  
- Python + PyInstaller  

---

## 📜 License

MIT License

---

## ❤️ Credits

- The LOTRO community  
- Open-source TTS and NLP projects  
- Contributors and testers  

---

## 🚀 Future Plans

- Emotion-aware voice tuning  
- Improved NPC recognition  
- More voice models  
- Better UI and usability  
