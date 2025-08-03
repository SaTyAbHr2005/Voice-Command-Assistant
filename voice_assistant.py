import pyttsx3
import speech_recognition as sr
import os
import sys
import time
import datetime
import keyboard
import pyautogui
import wikipedia
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import string
from ctypes import windll
from win32com.shell import shell, shellcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QPushButton, QLabel, QHBoxLayout, QTextEdit, QScrollArea)
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QRadialGradient, QFont, QLinearGradient, QTextCursor

# Initialize Text-to-Speech Engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# Global variables
driver = None
current_folder_path = None

class AssistantThread(QThread):
    update_signal = pyqtSignal(str)
    command_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = True
        
    def run(self):
        while self.active:
            command = listen()
            if command:
                self.command_signal.emit(command)
                process_command(command)
                
    def stop(self):
        self.active = False

def speak(text):
    """Speaks the given text and updates the GUI"""
    global gui_window
    print(f"Bunty: {text}")
    engine.say(text)
    engine.runAndWait()
    
    if 'gui_window' in globals() and gui_window:
        gui_window.process_user_command(f"Bunty: {text}")

def listen():
    """Listens to user input and updates the GUI"""
    global gui_window
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.pause_threshold = 1.0
        recognizer.energy_threshold = 400
        
        if 'gui_window' in globals() and gui_window:
            gui_window.update_status("Listening...")
            gui_window.process_user_command("User: ...")

        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
            command = recognizer.recognize_google(audio, language="en-IN")
            
            if 'gui_window' in globals() and gui_window:
                gui_window.process_user_command(f"User: {command}")
                gui_window.update_status("Processing...")
                
            print(f"You said: {command}")
            return command.lower()
            
        except sr.WaitTimeoutError:
            if 'gui_window' in globals() and gui_window:
                gui_window.process_user_command("Bunty: No speech detected, please try again.")
                gui_window.update_status("Ready")
            print("Bunty: No speech detected, please try again.")
            return ""
        except sr.UnknownValueError:
            if 'gui_window' in globals() and gui_window:
                gui_window.process_user_command("Bunty: Sorry, I couldn't understand. Please repeat.")
                gui_window.update_status("Ready")
            print("Bunty: Sorry, I couldn't understand. Please repeat.")
            return ""
        except sr.RequestError:
            if 'gui_window' in globals() and gui_window:
                gui_window.process_user_command("Bunty: Check your internet connection.")
                gui_window.update_status("Error")
            print("Bunty: Check your internet connection.")
            return ""

def find_search_bar():
    """Dynamically finds the search bar on a website."""
    possible_selectors = [
        "input[type='search']",
        "input[type='text']",
        "input[name='q']",
        "input[name='search']",
        "input[id='search']",
        "input[placeholder*='Search']",
        "input[aria-label*='Search']",
        "input[class*='search']",
        "form input[type='text']"
    ]
    
    for selector in possible_selectors:
        try:
            search_box = driver.find_element(By.CSS_SELECTOR, selector)
            return search_box
        except:
            continue
    return None

def close_browser():
    global driver
    if driver:
        driver.quit()
        driver = None
        speak("Closing Chrome browser.")

def open_search(command):
    try:
        # Open Windows Search
        keyboard.press_and_release("win+s")
        time.sleep(1.5)  

        # Type the command
        pyautogui.write(command, interval=0.1)
        time.sleep(2)

        # Press Enter to open the first result
        keyboard.press_and_release("enter")
        speak(f"Opening {command}")
    except Exception as e:
        print("Error:", e)
        speak(f"Sorry, I couldn't open {command}.")

def open_app(app_name):
    open_search(app_name)

def get_drives():
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(f"{letter}:\\")
        bitmask >>= 1
    return drives

def get_special_folder(folder_name):
    folder_name = folder_name.lower()
    
    # First try known environment variables
    folder_mapping = {
        'desktop': 'DESKTOP',
        'documents': 'DOCUMENTS',
        'downloads': 'DOWNLOAD',
        'music': 'MUSIC',
        'pictures': 'PICTURES',
        'videos': 'VIDEOS'
    }
    
    # Try environment variables first
    if folder_name in folder_mapping:
        try:
            env_var = folder_mapping[folder_name]
            path = os.path.join(os.environ['USERPROFILE'], env_var)
            if os.path.exists(path):
                return path
        except:
            pass
    
    # Try common OneDrive locations
    onedrive_path = os.path.join(os.path.expanduser('~'), 'OneDrive')
    if os.path.exists(onedrive_path):
        possible_path = os.path.join(onedrive_path, folder_name.capitalize())
        if os.path.exists(possible_path):
            return possible_path
    
    # Try direct path in user profile
    default_path = os.path.join(os.path.expanduser('~'), folder_name.capitalize())
    if os.path.exists(default_path):
        return default_path
    
    # Try shell folders as last resort
    try:
        folder_id = {
            'desktop': shellcon.CSIDL_DESKTOP,
            'documents': shellcon.CSIDL_MYDOCUMENTS,
            'downloads': shellcon.CSIDL_PROFILE,
            'pictures': shellcon.CSIDL_MYPICTURES,
            'music': shellcon.CSIDL_MYMUSIC,
            'videos': shellcon.CSIDL_MYVIDEO
        }.get(folder_name)
        
        if folder_id:
            path = shell.SHGetFolderPath(0, folder_id, None, 0)
            if os.path.exists(path):
                return path
    except:
        pass
    
    # Final fallback - check common locations
    common_locations = [
        os.path.join(os.path.expanduser('~'), 'OneDrive', folder_name.capitalize()),
        os.path.join(os.path.expanduser('~'), folder_name.capitalize()),
        os.path.join(os.environ['USERPROFILE'], folder_name.capitalize()),
        r'C:\Users\{}\{}'.format(os.getlogin(), folder_name.capitalize())
    ]
    
    for location in common_locations:
        if os.path.exists(location):
            return location
    
    return None

def find_subfolder_recursive(root_path, target_folder):
    target_folder_clean = "".join(e for e in target_folder if e.isalnum()).lower()
    matches = []
    
    for root, dirs, files in os.walk(root_path):
        for dir_name in dirs:
            dir_clean = "".join(e for e in dir_name if e.isalnum()).lower()
            if target_folder_clean == dir_clean:
                return os.path.join(root, dir_name)
            elif target_folder_clean in dir_clean:
                matches.append(os.path.join(root, dir_name))
    
    if matches:
        return matches[0]
    
    return None

def search_in_single_location(folder_name, search_path, recursive=False):
    global current_folder_path
    clean_folder_name = "".join(e for e in folder_name if e.isalnum()).lower()
    matches = []
    
    try:
        if recursive:
            # Perform recursive search
            found_path = find_subfolder_recursive(search_path, folder_name)
            if found_path:
                os.startfile(found_path)
                speak(f"Opening folder: {os.path.basename(found_path)}")
                current_folder_path = found_path
                return handle_folder_contents(found_path)
            else:
                speak(f"Sorry, I couldn't find a folder named {folder_name} in that location.")
                return False
        else:
            # First check direct children of the search path
            for item in os.listdir(search_path):
                item_path = os.path.join(search_path, item)
                if os.path.isdir(item_path):
                    clean_item = "".join(e for e in item if e.isalnum()).lower()
                    if clean_folder_name == clean_item:
                        os.startfile(item_path)
                        speak(f"Opening folder: {item}")
                        current_folder_path = item_path
                        return handle_folder_contents(item_path)
                    elif clean_folder_name in clean_item:
                        matches.append(item_path)
            
            if matches:
                return handle_multiple_matches(matches)
            else:
                speak(f"I couldn't find {folder_name} in this location. Should I search in subfolders?")
                response = listen().lower()
                if "yes" in response or "search" in response:
                    return search_in_single_location(folder_name, search_path, recursive=True)
                else:
                    speak(f"Okay, not searching further for {folder_name}.")
                    return False
                
    except Exception as e:
        print("Error:", e)
        speak("Sorry, there was an error accessing that location.")
        return False

def search_in_multiple_locations(folder_name, search_paths):
    clean_folder_name = "".join(e for e in folder_name if e.isalnum()).lower()
    matches = []
    
    for path in search_paths:
        try:
            if not os.path.exists(path):
                continue
                
            # First check direct children
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    clean_item = "".join(e for e in item if e.isalnum()).lower()
                    if clean_folder_name == clean_item:
                        os.startfile(item_path)
                        speak(f"Opening folder: {item}")
                        return handle_folder_contents(item_path)
                    elif clean_folder_name in clean_item:
                        matches.append(item_path)
            
            # If no direct matches, try recursive search in this path
            found_path = find_subfolder_recursive(path, folder_name)
            if found_path:
                os.startfile(found_path)
                speak(f"Opening folder: {os.path.basename(found_path)}")
                return handle_folder_contents(found_path)
                
        except Exception as e:
            print(f"Error searching in {path}:", e)
            continue
    
    if matches:
        return handle_multiple_matches(matches)
    else:
        speak(f"Sorry, I couldn't find a folder named {folder_name} in those locations.")
        return False

def handle_multiple_matches(matches):
    speak(f"I found {len(matches)} matching folders. The first one is named {os.path.basename(matches[0])}.")
    speak("Please say the exact name of the folder you want to open, or say 'cancel'.")
    
    while True:
        response = listen().lower()
        
        if "cancel" in response:
            speak("Okay, I won't open any folder.")
            return False
            
        if not response:
            speak("I didn't hear anything. Please try again.")
            continue
            
        # Search through all matches for the folder they requested
        clean_response = "".join(e for e in response if e.isalnum()).lower()
        found_folders = []
        
        for folder in matches:
            clean_folder = "".join(e for e in os.path.basename(folder) if e.isalnum()).lower()
            if clean_response in clean_folder:
                found_folders.append(folder)
                
        if len(found_folders) == 1:
            os.startfile(found_folders[0])
            speak(f"Opening folder: {os.path.basename(found_folders[0])}")
            return handle_folder_contents(found_folders[0])
        elif len(found_folders) > 1:
            speak(f"I found {len(found_folders)} folders matching '{response}'. Please be more specific.")
            continue
        else:
            speak(f"I couldn't find a folder matching '{response}'. Please try again.")

def open_folder(folder_name):
    global current_folder_path
    folder_name = folder_name.lower()
    
    # First check if it's a special folder we can open directly
    special_path = get_special_folder(folder_name)
    if special_path:
        try:
            if os.path.exists(special_path):
                os.startfile(special_path)
                current_folder_path = special_path
                speak(f"Opening {folder_name}")
                return handle_folder_contents(special_path)
            else:
                speak(f"I found the {folder_name} folder path but it doesn't exist: {special_path}")
        except Exception as e:
            print(f"Error opening folder: {e}")
            speak(f"Sorry, I couldn't open the {folder_name} folder.")
        return False
    
    # Otherwise ask where to search
    speak("Where should I search? You can say Desktop, Documents, Downloads, Pictures, Music, Videos, or a drive like C drive")
    location = listen().lower()
    
    # Determine search path
    search_path = None
    location_map = {
        'desktop': 'desktop',
        'document': 'documents',
        'download': 'downloads',
        'picture': 'pictures',
        'music': 'music',
        'video': 'videos'
    }
    
    # Check for mapped locations first
    for key in location_map:
        if key in location:
            search_path = get_special_folder(location_map[key])
            break
    
    # Check for drive letters if no special folder found
    if not search_path:
        drives = {
            'c drive': 'C:\\',
            'c:': 'C:\\',
            'd drive': 'D:\\',
            'd:': 'D:\\',
            'e drive': 'E:\\',
            'e:': 'E:\\'
        }
        for drive_key in drives:
            if drive_key in location:
                search_path = drives[drive_key]
                break
    
    if not search_path:
        speak("I'll search in common locations.")
        search_paths = [
            get_special_folder('desktop'),
            get_special_folder('documents'),
            get_special_folder('downloads'),
            get_special_folder('pictures'),
            "C:\\",
            "D:\\"
        ]
        # Filter out None paths and paths that don't exist
        search_paths = [path for path in search_paths if path and os.path.exists(path)]
        
        if search_paths:
            return search_in_multiple_locations(folder_name, search_paths)
        else:
            speak("Sorry, I couldn't find any accessible locations to search.")
            return False
    
    if not os.path.exists(search_path):
        speak(f"Sorry, I couldn't access {search_path}.")
        return False
    
    current_folder_path = search_path
    return search_in_single_location(folder_name, search_path)

def handle_folder_contents(folder_path):
    global current_folder_path
    time.sleep(2)
    
    try:
        if not os.path.exists(folder_path):
            speak("Sorry, I can't access that folder.")
            return False
        
        contents = os.listdir(folder_path)
        
        if not contents:
            speak("This folder is empty.")
            # Get parent folder path
            parent_path = os.path.dirname(folder_path)
            
            # Check if we can go back (not at root directory)
            if os.path.exists(parent_path) and parent_path != folder_path:
                while True:
                    speak("Would you like to go back to the parent folder? Say 'yes' or 'no'.")
                    action = listen().lower()
                    
                    if "yes" in action or "go back" in action:
                        current_folder_path = parent_path
                        os.startfile(parent_path)
                        speak("Going back to the parent folder.")
                        return handle_folder_contents(parent_path)
                    elif "no" in action or "exit" in action:
                        speak("Closing folder interaction.")
                        return True
                    else:
                        speak("I didn't understand. Please say 'yes' or 'no'.")
            else:
                speak("This is the root directory. Cannot go back further.")
                speak("Closing folder interaction.")
                return True
            
        files = [f for f in contents if os.path.isfile(os.path.join(folder_path, f))]
        subfolders = [f for f in contents if os.path.isdir(os.path.join(folder_path, f))]
        
        if files and subfolders:
            speak(f"This folder contains {len(files)} files and {len(subfolders)} subfolders.")
        elif files:
            speak(f"This folder contains {len(files)} files.")
        elif subfolders:
            speak(f"This folder contains {len(subfolders)} subfolders.")

        speak("What would you like to do? You can say 'open file', 'open folder', 'go back', or 'exit'.")
        
        while True:
            action = listen()
                
            if "exit" in action:
                speak("Closing folder interaction.")
                return True
                
            elif "go back" in action:
                parent_path = os.path.dirname(current_folder_path)
                if os.path.exists(parent_path) and parent_path != current_folder_path:
                    current_folder_path = parent_path
                    os.startfile(parent_path)
                    speak("Going back to the parent folder.")
                    return handle_folder_contents(parent_path)
                else:
                    speak("Cannot go back further.")
                    continue
                    
            elif "open file" in action:
                if not files:
                    speak("There are no files in this folder.")
                    continue
                    
                speak("Please say the name of the file you want to open.")
                file_name = listen()
                    
                if not file_name:
                    speak("No file specified.")
                    continue
                    
                clean_file_name = "".join(e for e in file_name if e.isalnum()).lower()
                found_files = [f for f in files if clean_file_name in "".join(e for e in f if e.isalnum()).lower()]
                
                if not found_files:
                    speak("No matching files found.")
                elif len(found_files) == 1:
                    os.startfile(os.path.join(folder_path, found_files[0]))
                    speak(f"Opening {found_files[0]}")
                else:
                    speak(f"I found {len(found_files)} matching files. Opening the first one: {found_files[0]}")
                    os.startfile(os.path.join(folder_path, found_files[0]))
                    
            elif "open folder" in action:
                if not subfolders:
                    speak("There are no subfolders in this folder.")
                    continue
                    
                speak("Please say the name of the subfolder you want to open.")
                subfolder_name = listen()
                    
                if not subfolder_name:
                    speak("No subfolder specified.")
                    continue
                    
                clean_subfolder_name = "".join(e for e in subfolder_name if e.isalnum()).lower()
                found_subfolders = [f for f in subfolders if clean_subfolder_name in "".join(e for e in f if e.isalnum()).lower()]
                
                if not found_subfolders:
                    speak("No matching subfolders found.")
                elif len(found_subfolders) == 1:
                    subfolder_path = os.path.join(folder_path, found_subfolders[0])
                    os.startfile(subfolder_path)
                    speak(f"Opening {found_subfolders[0]}")
                    current_folder_path = subfolder_path
                    return handle_folder_contents(subfolder_path)
                else:
                    speak(f"I found {len(found_subfolders)} matching subfolders. Opening the first one: {found_subfolders[0]}")
                    subfolder_path = os.path.join(folder_path, found_subfolders[0])
                    os.startfile(subfolder_path)
                    current_folder_path = subfolder_path
                    return handle_folder_contents(subfolder_path)
                    
            else:
                speak("I didn't understand. You can say 'open file', 'open folder', 'go back', or 'exit'.")
                
    except Exception as e:
        print("Error:", e)
        speak("Sorry, there was an error accessing the folder contents.")
        return False 

def open_file(file_name):
    home_dir = str(Path.home())
    clean_file_name = "".join(e for e in file_name if e.isalnum()).lower()
    found_file = None
    valid_extensions = ['.pdf', '.ppt', '.docx']

    for root, _, files in os.walk(home_dir):
        for file in files:
            clean_file = "".join(e for e in file if e.isalnum()).lower()
            for ext in valid_extensions:
                if clean_file_name in clean_file and file.endswith(ext):
                    found_file = os.path.join(root, file)
                    break
            if found_file:
                break
        if found_file:
            break

    if found_file:
        os.startfile(found_file)
        speak(f"Opening file: {os.path.basename(found_file)}")
    else:
        speak("Sorry, I couldn't find the specified file.")
        return

    speak("Say 'exit' when you want to close the file.")
    while True:
        command = listen()
        if "exit" in command:
            os.system("taskkill /F /IM " + os.path.basename(found_file))
            speak("Closing file.")
            break

    speak("Exiting file function.")

def get_time_date():
    now = datetime.datetime.now()
    speak(f"The current time is {now.strftime('%I:%M %p')}")
    speak(f"Today's date is {now.strftime('%B %d, %Y')}")

def search_wikipedia(query):
    try:
        result = wikipedia.summary(query, sentences=2)
        speak(f"According to Wikipedia: {result}")
    except:
        speak("Sorry, I couldn't find any information on that.")

def open_website_with_search(website_name):
    global driver
    starting_page = website_name  

    if not website_name.startswith(("http://", "https://")):
        website_name = f"https://www.{website_name}.com"

    while True:
        speak(f"Open {starting_page}?")
        confirmation = listen().lower()
        
        # Check for positive response
        if "dont" not in confirmation and "don" not in confirmation and "open" in confirmation:
            break
            
        # Check for negative response
        elif ("don't open" in confirmation) or ("dont open" in confirmation):
            speak("Okay, not opening it.")
            return
            
        # Unclear response
        else:
            speak("Please say 'open' or 'don't open'.")
            continue

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_experimental_option("detach", True)

    if driver is not None:
        try:
            current_url = driver.current_url
            if website_name in current_url:
                speak(f"{website_name} is already open. Switching to it.")
                driver.switch_to.window(driver.window_handles[0])
                driver.get(website_name)
            else:
                found = False
                for handle in driver.window_handles:
                    driver.switch_to.window(handle)
                    if website_name in driver.current_url:
                        found = True
                        break
                
                if found:
                    speak(f"Found {website_name} in another tab. Switching to it.")
                else:
                    speak(f"Opening {website_name} in the current window.")
                    driver.get(website_name)
        except:
            speak(f"Opening {website_name}")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(website_name)
    else:
        speak(f"Opening {website_name}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(website_name)
    
    time.sleep(3)

    # Original command prompts unchanged
    speak(f"You're now on {starting_page}. You can say commands like:")
    speak("'search something' to search on this site")
    speak("'previous page' to go back")
    speak("'next page' to go forward") 
    speak("'home page' to return to the main page")
    speak("'exit website' to stop browsing")

    # Original command handling unchanged
    while True:
        command = listen().lower()
        
        if not command:
            continue
            
        if "search" in command:
            query = command.replace("search", "").strip()
            if query:
                search_box = find_search_bar()
                if search_box:
                    search_box.clear()
                    search_box.send_keys(query)
                    time.sleep(1)
                    search_box.send_keys(Keys.RETURN)
                    speak(f"Searching for {query}")
                else:
                    speak("I couldn't find the search bar on this page.")
        
        elif "previous page" in command or "go back" in command:
            driver.back()
            speak("Going back to the previous page.")
            
        elif "next page" in command or "go forward" in command:
            driver.forward()
            speak("Going forward to the next page.")
            
        elif "home page" in command or "starting page" in command:
            if not starting_page.startswith(("http://", "https://")):
                starting_page = f"https://www.{starting_page}.com"
            driver.get(starting_page)
            speak("Returning to the home page.")
                
        elif "exit website" in command or "stop browsing" in command:
            speak("Closing the website. Say 'open website' if you want to browse again.")
            driver.quit()
            driver = None
            return
            
        else:
            continue

def process_command(command):
    print(f"Processing command: {command}")
    if not command:
        speak("I didn't hear anything. Please try again.")
        return

    command = command.lower()
    
    if "open" in command:
        if "website" in command:
            website_name = command.replace("open website", "").strip()
            open_website_with_search(website_name)
        elif "app" in command:
            app_name = command.replace("open app", "").strip()
            open_app(app_name)
        elif "folder" in command:
            folder_name = command.replace("open folder", "").strip()
            if not folder_name:
                speak("Which folder would you like to open?")
                folder_name = listen()
            open_folder(folder_name)
        elif "file" in command:
            file_name = command.replace("open file", "").strip()
            open_file(file_name)
        else:
            target = command.replace("open", "").strip()
            if target:
                if get_special_folder(target):
                    open_folder(target)
                elif os.path.isdir(target):
                    open_folder(target)
                else:
                    open_app(target)
            else:
                speak("Please specify what to open (e.g., website, app, folder, file).")

    elif "search" in command:
        query = command.replace("search", "").strip()
        search_wikipedia(query)
    elif "time" in command or "date" in command:
        get_time_date()
    elif "exit" in command or "bye" in command:
        speak("Goodbye! Have a nice day.")
        sys.exit()
    else:
        speak("I didn't understand that. Please try again.")

class GlowingCircleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.pulse_size = 0
        self.pulse_growing = True
        self.is_listening = False
        self.ripple_sets = [
            {"radius": 0, "alpha": 120, "active": False} for _ in range(30)
        ]
        self.current_ripple = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        main_radius = min(self.width(), self.height()) / 4
        
        gradient = QRadialGradient(center, main_radius + self.pulse_size)
        gradient.setColorAt(0, QColor(30, 144, 255, 200))
        gradient.setColorAt(0.7, QColor(30, 144, 255, 100))
        gradient.setColorAt(1, QColor(30, 144, 255, 0))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, main_radius + self.pulse_size, main_radius + self.pulse_size)
        
        painter.setBrush(QColor(30, 144, 255))
        painter.drawEllipse(center, main_radius - 10, main_radius - 10)
        
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        
        text_rect = painter.fontMetrics().boundingRect("Bunty")
        text_x = int(center.x() - (text_rect.width() / 2)) 
        text_y = int(center.y() + (text_rect.height() / 4)) 
        
        painter.drawText(text_x, text_y, "Bunty")
        
        if self.is_listening:
            for ripple in self.ripple_sets:
                if ripple["active"]:
                    alpha = ripple["alpha"]
                    radius = ripple["radius"]
                    
                    for i in range(3):
                        current_radius = radius + i*2
                        gradient = QRadialGradient(center, current_radius)
                        gradient.setColorAt(0, QColor(30, 144, 255, alpha//4))
                        gradient.setColorAt(0.5, QColor(100, 180, 255, alpha//2))
                        gradient.setColorAt(1, QColor(30, 144, 255, 0))
                        
                        painter.setBrush(gradient)
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(center, current_radius, current_radius)

    def update_animation(self):
        if self.pulse_growing:
            self.pulse_size += 0.5
            if self.pulse_size >= 10:
                self.pulse_growing = False
        else:
            self.pulse_size -= 0.5
            if self.pulse_size <= 0:
                self.pulse_growing = True
        
        if self.is_listening:
            if self.current_ripple % 10 == 0:
                for i in range(10):
                    idx = (self.current_ripple + i) % 30
                    if not self.ripple_sets[idx]["active"]:
                        self.ripple_sets[idx] = {
                            "radius": 50, 
                            "alpha": 120,
                            "active": True
                        }
                        break
            
            self.current_ripple += 1
            
            for ripple in self.ripple_sets:
                if ripple["active"]:
                    ripple["radius"] += 1.5
                    ripple["alpha"] -= 2
                    if ripple["alpha"] <= 0:
                        ripple["active"] = False
        
        self.update()
    
    def start_listening(self):
        self.is_listening = True
        self.ripple_sets = [
            {"radius": 0, "alpha": 120, "active": False} for _ in range(30)
        ]
        self.current_ripple = 0
    
    def stop_listening(self):
        self.is_listening = False

class VoiceAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bunty Voice Assistant")
        
        screen_geometry = QApplication.desktop().screenGeometry()
        width = 500
        height = 700
        self.setGeometry(
            (screen_geometry.width() - width) // 2,
            (screen_geometry.height() - height) // 2,
            width,
            height
        )
        
        self.setStyleSheet("background-color: #121212;")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setSpacing(20)

        self.layout.addStretch()  

        self.circle_container = QWidget()
        self.circle_layout = QHBoxLayout(self.circle_container)
        self.circle_layout.setAlignment(Qt.AlignCenter) 

        self.glowing_circle = GlowingCircleWidget()
        self.glowing_circle.setFixedSize(300, 300)

        self.circle_layout.addWidget(self.glowing_circle)
        self.circle_container.setLayout(self.circle_layout)

        self.layout.addWidget(self.circle_container, alignment=Qt.AlignCenter)

        self.layout.addStretch()  

        self.subtitle_label = QLabel("Your Personal Voice Assistant")
        self.subtitle_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 16px;
                font-family: 'Arial';
            }
        """)
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.subtitle_label)

        self.conversation_scroll = QScrollArea()
        self.conversation_scroll.setWidgetResizable(True)
        self.conversation_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #333;
                border-radius: 5px;
                background-color: #1e1e1e;
            }
        """)

        self.conversation_text = QTextEdit()
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Arial';
                font-size: 14px;
                border: none;
                padding: 10px;
            }
        """)
        self.conversation_scroll.setWidget(self.conversation_text)
        self.conversation_scroll.setMinimumHeight(200)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(20)
        self.buttons_layout.setAlignment(Qt.AlignCenter)

        self.listen_button = QPushButton("Start Listening")
        self.listen_button.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1a7fdd;
            }
        """)
        self.listen_button.clicked.connect(self.toggle_listening)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4757;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e8413d;
            }
        """)
        self.exit_button.clicked.connect(self.close)

        self.buttons_layout.addWidget(self.listen_button)
        self.buttons_layout.addWidget(self.exit_button)

        self.status_label = QLabel("Ready to assist you")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 14px;
                font-family: 'Arial';
            }
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(30)

        self.layout.addWidget(self.conversation_scroll)
        self.layout.addLayout(self.buttons_layout)
        self.layout.addWidget(self.status_label)

        self.layout.setContentsMargins(20, 20, 20, 20)

        self.recognizer = sr.Recognizer()
        self.is_active_listening = False

        self.assistant_thread = AssistantThread()
        self.assistant_thread.update_signal.connect(self.update_status)
        self.assistant_thread.command_signal.connect(self.process_user_command)

    def process_user_command(self, text):
        if text: 
            self.conversation_text.append(text)
            self.conversation_text.moveCursor(QTextCursor.End)

    def update_status(self, text):
        self.status_label.setText(text)

    def toggle_listening(self):
        if not self.is_active_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        self.is_active_listening = True
        self.glowing_circle.is_listening = True
        self.glowing_circle.start_listening()
        self.listen_button.setText("Stop Listening")
        self.update_status("Listening... Speak now")

        if not self.assistant_thread.isRunning():
            self.assistant_thread.start()

    def stop_listening(self):
        self.is_active_listening = False
        self.glowing_circle.is_listening = False
        self.glowing_circle.stop_listening()
        self.listen_button.setText("Start Listening")
        self.update_status("Ready to assist you")

    def closeEvent(self, event):
        if self.assistant_thread.isRunning():
            self.assistant_thread.stop()
            self.assistant_thread.quit()
            self.assistant_thread.wait()
        event.accept()


gui_window = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = VoiceAssistantGUI()
    gui_window = window 
    window.show()
    
    current_hour = datetime.datetime.now().hour
    
    if 5 <= current_hour < 12:
        greeting = "Good morning! I am Bunty, your voice assistant. How can I assist you?"
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon! I am Bunty, your voice assistant. How can I help you?"
    elif 17 <= current_hour < 21:
        greeting = "Good evening! I am Bunty, your voice assistant. What can I do for you?"
    else:
        greeting = "Hello! I am Bunty, your voice assistant. How can I assist you?"
    
    speak(greeting)    
    sys.exit(app.exec_())