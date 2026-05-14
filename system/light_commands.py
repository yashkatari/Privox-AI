"""
Enhanced System Commands for PriVox AI Assistant
WITH better command recognition and all common apps
"""
import os
import sys
import subprocess
import platform
import webbrowser
import datetime
import time
import random
from pathlib import Path

class EnhancedSystemCommands:
    def __init__(self):
        self.system = platform.system()
        self.home_dir = str(Path.home())
        
        # Expanded command mapping with ALL common apps
        self.command_map = {
            # Web Applications
            'open whatsapp': self.open_whatsapp,
            'open chatgpt': self.open_chatgpt,
            'open google': self.open_google,
            'open youtube': self.open_youtube,
            'open github': self.open_github,
            'open linkedin': self.open_linkedin,
            'open browser': self.open_browser,
            'open gmail': self.open_gmail,
            'open drive': self.open_drive,
            'open maps': self.open_maps,
            'open calendar': self.open_calendar,
            'open spotify': self.open_spotify,
            'open netflix': self.open_netflix,
            'open instagram': self.open_instagram,
            'open facebook': self.open_facebook,
            'open twitter': self.open_twitter,
            
            # System Applications
            'open file manager': self.open_file_manager,
            'open file explorer': self.open_file_manager,
            'open terminal': self.open_terminal,
            'open command prompt': self.open_terminal,
            'open powershell': self.open_powershell,
            'open notepad': self.open_notepad,
            'open calculator': self.open_calculator,
            'open paint': self.open_paint,
            'open word': self.open_word,
            'open excel': self.open_excel,
            'open powerpoint': self.open_powerpoint,
            'open camera': self.open_camera,
            'open media player': self.open_media_player,
            'open photos': self.open_photos_app,
            'open mail': self.open_mail_app,
            'open store': self.open_store,
            
            # File operations
            'open documents': self.open_documents,
            'open downloads': self.open_downloads,
            'open desktop': self.open_desktop,
            'open pictures': self.open_pictures,
            'open music': self.open_music,
            'open videos': self.open_videos,
            
            # System Controls
            'take screenshot': self.take_screenshot,
            'capture screen': self.take_screenshot,
            'screenshot': self.take_screenshot,
            'lock screen': self.lock_screen,
            'open settings': self.open_settings,
            'shutdown': self.shutdown,
            'restart': self.restart,
            'sleep': self.sleep,
            'log off': self.logoff,
        }
        
        # Command variations for better recognition
        self.command_variations = {
            'whatsapp': ['whats app', 'whatsapp web', 'whatsapp app'],
            'chatgpt': ['chat gpt', 'open ai', 'gpt'],
            'google': ['search', 'browse', 'web'],
            'youtube': ['video', 'watch', 'tube'],
            'file manager': ['explorer', 'files', 'folder', 'documents'],
            'calculator': ['calc', 'math'],
            'terminal': ['cmd', 'command', 'powershell', 'shell'],
            'notepad': ['text editor', 'write', 'notes'],
            'screenshot': ['capture', 'screen shot', 'print screen'],
            'settings': ['control panel', 'config', 'preferences'],
        }
    
    def execute_command(self, text):
        """Execute system command based on voice/text input"""
        text = text.lower().strip()
        
        print(f"[System Command] Checking: '{text}'")
        
        # Clean up common filler words
        filler_words = ['please', 'can you', 'could you', 'would you', 
                       'hey', 'okay', 'ok', 'hi', 'hello', 'privox']
        for word in filler_words:
            text = text.replace(word, '').strip()
        
        # Remove "open" if present for better matching
        clean_text = text.replace('open', '').strip()
        
        print(f"[System Command] Cleaned: '{clean_text}'")
        
        # Strategy 1: Direct exact match
        for cmd, func in self.command_map.items():
            cmd_key = cmd.replace('open ', '').strip()
            if cmd_key in clean_text or cmd in text:
                print(f"[System Command] Exact match: '{cmd}'")
                try:
                    result = func()
                    return True, f"🚀 {result}"
                except Exception as e:
                    return False, f"❌ Error: {str(e)}"
        
        # Strategy 2: Partial word matching
        import re
        for cmd, func in self.command_map.items():
            cmd_words = cmd.split()
            # Must contain ALL non-filler words of the command entirely, 
            # to avoid false positives like 'word' matching inside 'password'.
            required_words = [w for w in cmd_words if w != 'open']
            
            # Check if we should trigger
            if required_words and all(re.search(rf'\b{re.escape(w)}\b', clean_text) for w in required_words):
                print(f"[System Command] Advanced Partial match: '{cmd}' in '{clean_text}'")
                try:
                    result = func()
                    return True, f"🚀 {result}"
                except Exception as e:
                    return False, f"❌ Error: {str(e)}"
        
        # Strategy 3: Check variations
        for base_cmd, variations in self.command_variations.items():
            full_cmd = f"open {base_cmd}"
            if full_cmd in self.command_map:
                for variation in variations:
                    if variation in clean_text:
                        print(f"[System Command] Variation: '{variation}' -> '{full_cmd}'")
                        try:
                            result = self.command_map[full_cmd]()
                            return True, f"🚀 {result}"
                        except Exception as e:
                            return False, f"❌ Error: {str(e)}"
        
        # Strategy 4: Common app names
        app_mapping = {
            'whatsapp': self.open_whatsapp,
            'google': self.open_google,
            'youtube': self.open_youtube,
            'file': self.open_file_manager,
            'explorer': self.open_file_manager,
            'calc': self.open_calculator,
            'terminal': self.open_terminal,
            'cmd': self.open_terminal,
            'notepad': self.open_notepad,
            'screenshot': self.take_screenshot,
            'settings': self.open_settings,
            'github': self.open_github,
            'linkedin': self.open_linkedin,
            'browser': self.open_browser,
            'chatgpt': self.open_chatgpt,
            'gpt': self.open_chatgpt,
            'photos': self.open_pictures,
            'music': self.open_music,
            'videos': self.open_videos,
            'documents': self.open_documents,
            'downloads': self.open_downloads,
            'desktop': self.open_desktop,
        }
        
        for app_name, func in app_mapping.items():
            if app_name in clean_text:
                print(f"[System Command] App match: '{app_name}'")
                try:
                    result = func()
                    return True, f"🚀 {result}"
                except Exception as e:
                    return False, f"❌ Error: {str(e)}"
        
        print(f"[System Command] No match found for: '{text}'")
        return False, "Command not recognized. Try: 'open calculator', 'open whatsapp', 'open file manager', etc."
    
    # ======================
    # SCREENSHOT FUNCTION
    # ======================
    
    def take_screenshot(self):
        """Take screenshot using PIL/Pillow"""
        try:
            from PIL import ImageGrab
            
            screenshot = ImageGrab.grab()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            screenshot.save(filename)
            
            width, height = screenshot.size
            file_size = os.path.getsize(filename) / 1024
            
            return f"📸 Screenshot saved: '{filename}' ({width}x{height}, {file_size:.1f} KB)"
            
        except ImportError:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.txt"
            
            placeholder = f"""SCREENSHOT INFO
            Time: {timestamp}
            Install Pillow for actual screenshots: pip install pillow"""
            
            with open(filename, 'w') as f:
                f.write(placeholder)
            
            return f"📸 Screenshot info saved: {filename} (Install Pillow: pip install pillow)"
            
        except Exception as e:
            return f"❌ Screenshot failed: {str(e)}"
    
    # ======================
    # WEB APPLICATIONS
    # ======================
    
    def open_whatsapp(self):
        webbrowser.open("https://web.whatsapp.com")
        return "Opening WhatsApp Web..."
    
    def open_chatgpt(self):
        webbrowser.open("https://chat.openai.com")
        return "Opening ChatGPT..."
    
    def open_google(self):
        webbrowser.open("https://www.google.com")
        return "Opening Google..."
    
    def open_youtube(self):
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube..."
    
    def open_github(self):
        webbrowser.open("https://github.com")
        return "Opening GitHub..."
    
    def open_linkedin(self):
        webbrowser.open("https://linkedin.com")
        return "Opening LinkedIn..."
    
    def open_browser(self):
        webbrowser.open("https://www.google.com")
        return "Opening web browser..."
    
    def open_gmail(self):
        webbrowser.open("https://mail.google.com")
        return "Opening Gmail..."
    
    def open_drive(self):
        webbrowser.open("https://drive.google.com")
        return "Opening Google Drive..."
    
    def open_maps(self):
        webbrowser.open("https://maps.google.com")
        return "Opening Google Maps..."
    
    def open_calendar(self):
        webbrowser.open("https://calendar.google.com")
        return "Opening Google Calendar..."
    
    def open_spotify(self):
        webbrowser.open("https://open.spotify.com")
        return "Opening Spotify..."
    
    def open_netflix(self):
        webbrowser.open("https://netflix.com")
        return "Opening Netflix..."
    
    def open_instagram(self):
        webbrowser.open("https://instagram.com")
        return "Opening Instagram..."
    
    def open_facebook(self):
        webbrowser.open("https://facebook.com")
        return "Opening Facebook..."
    
    def open_twitter(self):
        webbrowser.open("https://twitter.com")
        return "Opening Twitter..."
    
    # ======================
    # SYSTEM APPLICATIONS
    # ======================
    
    def open_file_manager(self):
        if self.system == "Windows":
            subprocess.Popen(["explorer"])
            return "Opening File Explorer..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Finder"])
            return "Opening Finder..."
        else:
            subprocess.Popen(["xdg-open", self.home_dir])
            return "Opening file manager..."
    
    def open_terminal(self):
        if self.system == "Windows":
            subprocess.Popen(["cmd"])
            return "Opening Command Prompt..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Terminal"])
            return "Opening Terminal..."
        else:
            subprocess.Popen(["gnome-terminal"])
            return "Opening terminal..."
    
    def open_powershell(self):
        if self.system == "Windows":
            subprocess.Popen(["powershell"])
            return "Opening PowerShell..."
        else:
            return self.open_terminal()
    
    def open_notepad(self):
        if self.system == "Windows":
            subprocess.Popen(["notepad"])
            return "Opening Notepad..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "TextEdit"])
            return "Opening TextEdit..."
        else:
            subprocess.Popen(["gedit"])
            return "Opening text editor..."
    
    def open_calculator(self):
        if self.system == "Windows":
            subprocess.Popen(["calc"])
            return "Opening Calculator..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Calculator"])
            return "Opening Calculator..."
        else:
            subprocess.Popen(["gnome-calculator"])
            return "Opening calculator..."
    
    def open_paint(self):
        if self.system == "Windows":
            subprocess.Popen(["mspaint"])
            return "Opening Paint..."
        else:
            return "Paint not available on this system"
    
    def open_word(self):
        if self.system == "Windows":
            try:
                subprocess.Popen(["winword"])
                return "Opening Microsoft Word..."
            except:
                return "Microsoft Word not found"
        else:
            return "Microsoft Word not available on this system"
    
    def open_excel(self):
        if self.system == "Windows":
            try:
                subprocess.Popen(["excel"])
                return "Opening Microsoft Excel..."
            except:
                return "Microsoft Excel not found"
        else:
            return "Microsoft Excel not available on this system"
    
    def open_powerpoint(self):
        if self.system == "Windows":
            try:
                subprocess.Popen(["powerpnt"])
                return "Opening Microsoft PowerPoint..."
            except:
                return "Microsoft PowerPoint not found"
        else:
            return "Microsoft PowerPoint not available on this system"
    
    def open_camera(self):
        if self.system == "Windows":
            subprocess.Popen(["start", "microsoft.windows.camera:"], shell=True)
            return "Opening Camera..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Photo Booth"])
            return "Opening Camera..."
        else:
            subprocess.Popen(["cheese"])
            return "Opening camera..."
    
    def open_media_player(self):
        if self.system == "Windows":
            subprocess.Popen(["wmplayer"])
            return "Opening Media Player..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "QuickTime Player"])
            return "Opening QuickTime Player..."
        else:
            subprocess.Popen(["vlc"])
            return "Opening media player..."
    
    def open_photos_app(self):
        if self.system == "Windows":
            subprocess.Popen(["start", "microsoft.windows.photos:"], shell=True)
            return "Opening Photos app..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Photos"])
            return "Opening Photos app..."
        else:
            return self.open_pictures()
    
    def open_mail_app(self):
        if self.system == "Windows":
            subprocess.Popen(["start", "outlookmail:"], shell=True)
            return "Opening Mail app..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "Mail"])
            return "Opening Mail app..."
        else:
            return "Mail app not available"
    
    def open_store(self):
        if self.system == "Windows":
            subprocess.Popen(["start", "ms-windows-store:"], shell=True)
            return "Opening Microsoft Store..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "App Store"])
            return "Opening App Store..."
        else:
            return "App store not available"
    
    # ======================
    # FILE OPERATIONS
    # ======================
    
    def open_documents(self):
        docs_path = os.path.join(self.home_dir, "Documents")
        if os.path.exists(docs_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", docs_path])
            else:
                subprocess.Popen(["xdg-open", docs_path])
            return "Opening Documents folder..."
        return "Documents folder not found"
    
    def open_downloads(self):
        downloads_path = os.path.join(self.home_dir, "Downloads")
        if os.path.exists(downloads_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", downloads_path])
            else:
                subprocess.Popen(["xdg-open", downloads_path])
            return "Opening Downloads folder..."
        return "Downloads folder not found"
    
    def open_desktop(self):
        desktop_path = os.path.join(self.home_dir, "Desktop")
        if os.path.exists(desktop_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", desktop_path])
            else:
                subprocess.Popen(["xdg-open", desktop_path])
            return "Opening Desktop..."
        return "Desktop folder not found"
    
    def open_pictures(self):
        pictures_path = os.path.join(self.home_dir, "Pictures")
        if os.path.exists(pictures_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", pictures_path])
            else:
                subprocess.Popen(["xdg-open", pictures_path])
            return "Opening Pictures folder..."
        return "Pictures folder not found"
    
    def open_music(self):
        music_path = os.path.join(self.home_dir, "Music")
        if os.path.exists(music_path):
            if self.system == "Windows":
                subprocess.Popen(["explorer", music_path])
            else:
                subprocess.Popen(["xdg-open", music_path])
            return "Opening Music folder..."
        return "Music folder not found"
    
    def open_videos(self):
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
    
    def lock_screen(self):
        if self.system == "Windows":
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "🔒 Locking screen..."
        elif self.system == "Darwin":
            subprocess.Popen(["pmset", "displaysleepnow"])
            return "🔒 Locking screen..."
        else:
            try:
                subprocess.Popen(["gnome-screensaver-command", "-l"])
            except:
                try:
                    subprocess.Popen(["xdg-screensaver", "lock"])
                except:
                    pass
            return "🔒 Locking screen..."
    
    def open_settings(self):
        if self.system == "Windows":
            subprocess.Popen(["start", "ms-settings:"], shell=True)
            return "Opening Settings..."
        elif self.system == "Darwin":
            subprocess.Popen(["open", "-a", "System Preferences"])
            return "Opening System Preferences..."
        else:
            subprocess.Popen(["gnome-control-center"])
            return "Opening system settings..."
    
    def shutdown(self):
        if self.system == "Windows":
            subprocess.Popen(["shutdown", "/s", "/t", "10"])
            return "⏰ Shutting down in 10 seconds..."
        elif self.system == "Darwin":
            subprocess.Popen(["shutdown", "-h", "+1"])
            return "⏰ Shutting down in 1 minute..."
        else:
            subprocess.Popen(["shutdown", "-h", "+1"])
            return "⏰ Shutting down in 1 minute..."
    
    def restart(self):
        if self.system == "Windows":
            subprocess.Popen(["shutdown", "/r", "/t", "10"])
            return "🔄 Restarting in 10 seconds..."
        elif self.system == "Darwin":
            subprocess.Popen(["shutdown", "-r", "+1"])
            return "🔄 Restarting in 1 minute..."
        else:
            subprocess.Popen(["shutdown", "-r", "+1"])
            return "🔄 Restarting in 1 minute..."
    
    def sleep(self):
        if self.system == "Windows":
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "💤 Going to sleep..."
        elif self.system == "Darwin":
            subprocess.Popen(["pmset", "sleepnow"])
            return "💤 Going to sleep..."
        else:
            return "Sleep mode not available on this system"
    
    def logoff(self):
        if self.system == "Windows":
            subprocess.Popen(["shutdown", "/l"])
            return "👋 Logging off..."
        else:
            return "Log off not available on this system"
    
    # ======================
    # UTILITY METHODS
    # ======================
    
    def get_available_commands(self):
        """Return list of available commands"""
        commands = []
        for cmd in self.command_map.keys():
            cmd_display = cmd.replace('open ', '').title()
            commands.append(cmd_display)
        return commands
    
    def get_system_info(self):
        """Get system information"""
        import json
        info = {
            "System": self.system,
            "Platform": platform.platform(),
            "Home Directory": self.home_dir,
            "Python Version": platform.python_version(),
            "Available Commands": len(self.command_map)
        }
        return json.dumps(info, indent=2)

# Global instance
enhanced_system_commands = EnhancedSystemCommands()