# Bunty Voice Assistant

**Bunty** is a desktop-based voice assistant built with Python that can open apps, folders, files, and websites using your voice. It uses **speech recognition**, **text-to-speech**, **PyQt5 for GUI**, and other automation tools like **PyAutoGUI** and **Selenium** to interact with your system and the web — all hands-free.

---

## 🚀 Features

- **Natural Voice Interaction**  
  Talk to Bunty just like you would to a real assistant.

- **Open Applications & Files**  
  Say commands like “open Chrome” or “open my PDF” and let Bunty handle it.

- **Browse Websites via Voice**  
  Say “open website YouTube” and interact using voice-based browser navigation.

- **Folder Navigation & File Access**  
  Open, explore, and navigate through folders via voice.

- **Wikipedia Search**  
  Get summarized answers from Wikipedia with a simple voice command.

- **Real-Time GUI Feedback**  
  See Bunty's thoughts and responses with a glowing animation and chat-style interface.

---

## 🛠️ Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/bunty-voice-assistant.git
   cd bunty-voice-assistant

2. **Install Dependencies**

   Make sure you have Python 3.8+ installed.

   Then run:
   ```bash
   pip install -r requirements.txt

 If you don’t have a requirements.txt, here are the core dependencies:
 ```bash
 pip install pyttsx3 SpeechRecognition PyQt5 pyautogui wikipedia selenium keyboard pyaudio webdriver-manager
```

3. **Run the Assistant**
```bash
python voice_assistant.py
```

---

## 📌 Usage

- **Start Listening**  
  Click **"Start Listening"** in the GUI or speak once the app loads.

- **Supported Voice Commands**
  - “Open Chrome”, “Open Notepad”, “Open Calculator”
  - “Open folder Downloads”, “Open folder Documents”
  - “Open file resume.pdf”
  - “Open website YouTube”
  - “Search Albert Einstein” (Wikipedia)
  - “What’s the time?”, “What’s the date?”

- **End Session**  
  Say `"exit"` or `"bye"` to quit the assistant.

---

## 📁 File Structure

```text
bunty-voice-assistant/
├── voice_assistant.py        # Main application logic and GUI
├── assets/                   # (Optional) Folder for icons or assets
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies (optional)
```

---

## 💡 Notes
  -	Ensure your microphone is enabled and accessible.
  -	If using websites, Chrome will open via Selenium.
  -	This project is designed to run on Windows systems due to usage of certain Windows-specific paths and libraries.

---

### 🛠️ Built with Python, Designed for Productivity  
> 🧠 Meet **Bunty** — your smart, voice-activated desktop assistant.  
> 💬 Speak commands. Get things done. Hands-free.



