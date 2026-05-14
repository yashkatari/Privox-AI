"""
System Commands Module for PriVox AI Assistant
Enables voice-controlled system operations
"""
import os
import sys
import subprocess
import platform
import webbrowser
import time
from pathlib import Path
import json

class SystemCommands:
    def __init__(self):
        self.system = platform.system()
        self.home_dir = str(Path.home())
        
        # Command mapping with multiple triggers
        self.command_map = {
            # Web Applications
            'open whatsapp': self.open_whatsapp,
            'open chat gpt': self.open_chatgpt,
            'open google': self.open_google,
            'open youtube': self.open_youtube,
            'open github': self.open_github,
            'open linkedin': self.open_linkedin,
            
            # System Applications
            'open file manager': self.open_file_manager,
            'open file explorer': self.open_file_manager,
            'open documents': self.open_documents,
            'open downloads': self.open_downloads,
            'open desktop': self.open_desktop,
            
            # Productivity Apps
            'open notepad': self.open_notepad,
            'open calculator': self.open_calculator,
            'open terminal': self.open_terminal,
            'open command prompt': self.open_terminal,
            'open vs code': self.open_vscode,
            
            # Media & Entertainment
            'open camera': self.open_camera,
            'open music': self.open_music,
            'open photos': self.open_photos,
            'open videos': self.open_videos,
            
            # System Controls
            'take screenshot': self.take_screenshot,
            'copy to clipboard': self.copy_to_clipboard,
            'paste from clipboard': self.paste_from_clipboard,
            'lock screen': self.lock_screen,
            'show desktop': self.show_desktop,
            
            # Development Tools
            'open browser': self.open_browser,
            'open python': self.open_python,
            'open jupyter': self.open_jupyter,
        }
    
    def execute_command(self, text):
        """
        Execute system commands. Supports multiple consecutive commands.
        Returns: (success, message)
        """
        text = text.lower().strip()
        
        # Handle compound commands
        import re
        parts = re.split(r'\s+and\s+|\s+then\s+|,\s*', text)
        
        if len(parts) > 1:
            results = []
            any_success = False
            for part in parts:
                part = part.strip()
                if not part: continue
                
                success, msg = self._execute_single(part)
                if success:
                    any_success = True
                if msg != "Command not recognized.":
                    results.append(msg)
                    
            if any_success:
                return True, "Executed multiple actions:\n" + "\n".join([f"• {r}" for r in results])
            return False, "None of the commands were recognized."
            
        return self._execute_single(text)
        
    def _execute_single(self, text):
        """Executes a single split block"""
        # Check for exact matches first
        for cmd, func in self.command_map.items():
            if cmd in text:
                try:
                    result = func()
                    return True, result
                except Exception as e:
                    return False, f"Error: {str(e)}"
        
        # Check for partial matches
        import re
        for cmd, func in self.command_map.items():
            cmd_words = cmd.split()
            # Must contain ALL words in the command, or at least a significant overlap,
            # but currently looking for ANY word caused massive false positives.
            # E.g., 'word' in 'password' matched 'open word'.
            # A safer partial match: checking if all words are present as whole words.
            if all(re.search(rf'\b{re.escape(w)}\b', text) for w in cmd_words):
                try:
                    result = func()
                    return True, result
                except Exception as e:
                    return False, f"Error: {str(e)}"
        
        return False, "Command not recognized."
    
    # ======================
    # WEB APPLICATIONS
    # ======================
    
    def open_whatsapp(self):
        """Open WhatsApp Web"""
        webbrowser.open("https://web.whatsapp.com")
        return "Opening WhatsApp Web..."
    
    def open_chatgpt(self):
        """Open ChatGPT"""
        webbrowser.open("https://chat.openai.com")
        return "Opening ChatGPT..."
    
    def open_google(self):
        """Open Google"""
        webbrowser.open("https://www.google.com")
        return "Opening Google..."
    
    def open_youtube(self):
        """Open YouTube"""
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube..."
    
    def open_github(self):
        """Open GitHub"""
        webbrowser.open("https://github.com")
        return "Opening GitHub..."
    
    def open_linkedin(self):
        """Open LinkedIn"""
        webbrowser.open("https://linkedin.com")
        return "Opening LinkedIn..."
    
    # ======================
    # SYSTEM APPLICATIONS
    # ======================
    
    def open_file_manager(self):
        """Open system file manager"""
        if self.system == "Windows":
            subprocess.Popen(["explorer"])
        elif self.system == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", "Finder"])
        else:  # Linux
            subprocess.Popen(["xdg-open", self.home_dir])
        return "Opening file manager..."
    
    def open_documents(self):
        """Open Documents folder"""
        docs_path = os.path.join(self.home_dir, "Documents")
        if os.path.exists(docs_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", docs_path])
            else:
                subprocess.Popen(["xdg-open", docs_path])
            return "Opening Documents folder..."
        return "Documents folder not found"
    
    def open_downloads(self):
        """Open Downloads folder"""
        downloads_path = os.path.join(self.home_dir, "Downloads")
        if os.path.exists(downloads_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", downloads_path])
            else:
                subprocess.Popen(["xdg-open", downloads_path])
            return "Opening Downloads folder..."
        return "Downloads folder not found"
    
    def open_desktop(self):
        """Open Desktop folder"""
        desktop_path = os.path.join(self.home_dir, "Desktop")
        if os.path.exists(desktop_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", desktop_path])
            else:
                subprocess.Popen(["xdg-open", desktop_path])
            return "Opening Desktop..."
        return "Desktop folder not found"
    
    # ======================
    # PRODUCTIVITY APPS
    # ======================
    
    def open_notepad(self):
        """Open text editor"""
        if self.system == "Windows":
            subprocess.Popen(["notepad"])
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "TextEdit"])
        else:
            subprocess.Popen(["gedit"])
        return "Opening text editor..."
    
    def open_calculator(self):
        """Open calculator"""
        if self.system == "Windows":
            subprocess.Popen(["calc"])
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Calculator"])
        else:
            subprocess.Popen(["gnome-calculator"])
        return "Opening calculator..."
    
    def open_terminal(self):
        """Open terminal/command prompt"""
        if self.system == "Windows":
            subprocess.Popen(["cmd"])
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Terminal"])
        else:
            subprocess.Popen(["gnome-terminal"])
        return "Opening terminal..."
    
    def open_vscode(self):
        """Open Visual Studio Code"""
        try:
            if self.system == "Windows":
                subprocess.Popen(["code"])
            elif self.system == "Darwin":
                subprocess.Popen(["open", "-a", "Visual Studio Code"])
            else:
                subprocess.Popen(["code"])
            return "Opening Visual Studio Code..."
        except:
            return "Visual Studio Code not found"
    
    # ======================
    # MEDIA & ENTERTAINMENT
    # ======================
    
    def open_camera(self):
        """Open camera app"""
        if self.system == "Windows":
            subprocess.Popen(["start", "microsoft.windows.camera:"], shell=True)
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Photo Booth"])
        else:
            subprocess.Popen(["cheese"])
        return "Opening camera..."
    
    def open_music(self):
        """Open music folder or player"""
        music_path = os.path.join(self.home_dir, "Music")
        if os.path.exists(music_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", music_path])
            else:
                subprocess.Popen(["xdg-open", music_path])
            return "Opening Music folder..."
        return "Music folder not found"
    
    def open_photos(self):
        """Open photos folder"""
        pictures_path = os.path.join(self.home_dir, "Pictures")
        if os.path.exists(pictures_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", pictures_path])
            else:
                subprocess.Popen(["xdg-open", pictures_path])
            return "Opening Pictures folder..."
        return "Pictures folder not found"
    
    def open_videos(self):
        """Open videos folder"""
        videos_path = os.path.join(self.home_dir, "Videos")
        if os.path.exists(videos_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", videos_path])
            else:
                subprocess.Popen(["xdg-open", videos_path])
            return "Opening Videos folder..."
        return "Videos folder not found"
    
    # ======================
    # SYSTEM CONTROLS
    # ======================
    
    def take_screenshot(self):
        """Take and save screenshot"""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{int(time.time())}.png"
            screenshot.save(filename)
            return f"Screenshot saved as {filename}"
        except ImportError:
            return "pyautogui not installed for screenshots"
    
    def copy_to_clipboard(self):
        """Copy text to clipboard"""
        try:
            import pyperclip
            # You would need text to copy - this is a placeholder
            # In real usage, you'd pass text as parameter
            return "Ready to copy text. Say 'copy [text]'"
        except ImportError:
            return "pyperclip not installed for clipboard operations"
    
    def paste_from_clipboard(self):
        """Paste from clipboard"""
        try:
            import pyperclip
            text = pyperclip.paste()
            return f"Clipboard contains: {text[:50]}..."
        except ImportError:
            return "pyperclip not installed for clipboard operations"
    
    def lock_screen(self):
        """Lock the screen"""
        if self.system == "Windows":
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        elif self.system == "Darwin":
            subprocess.Popen(["pmset", "displaysleepnow"])
        else:
            subprocess.Popen(["gnome-screensaver-command", "-l"])
        return "Locking screen..."
    
    def show_desktop(self):
        """Show desktop (minimize all windows)"""
        if self.system == "Windows":
            subprocess.Popen(["powershell", "-Command", "(New-Object -ComObject Shell.Application).ToggleDesktop()"])
            return "Showing desktop..."
        elif self.system == "Darwin":
            subprocess.Popen(["osascript", "-e", 'tell application "System Events" to keystroke "d" using {command down}'])
            return "Showing desktop..."
        else:
            # Linux - varies by desktop environment
            return "Desktop show not supported on this system"
    
    # ======================
    # DEVELOPMENT TOOLS
    # ======================
    
    def open_browser(self):
        """Open default browser"""
        webbrowser.open("https://www.google.com")
        return "Opening web browser..."
    
    def open_python(self):
        """Open Python interpreter"""
        subprocess.Popen([sys.executable, "-i"])
        return "Opening Python interpreter..."
    
    def open_jupyter(self):
        """Try to open Jupyter Notebook"""
        try:
            subprocess.Popen(["jupyter", "notebook"])
            return "Opening Jupyter Notebook..."
        except:
            return "Jupyter Notebook not found"
    
    # ======================
    # UTILITY METHODS
    # ======================
    
    def get_available_commands(self):
        """Return list of available commands"""
        return list(self.command_map.keys())
    
    def get_system_info(self):
        """Get system information"""
        info = {
            "system": self.system,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "home_directory": self.home_dir
        }
        return json.dumps(info, indent=2)

# Global instance
system_commands = SystemCommands()