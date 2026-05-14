"""
Text-to-Speech module for PriVox AI Assistant - PERFECT WINDOWS SAPI VERSION
"""
import pyttsx3
import platform
import re
import threading
import queue
import time
import os

class TTSEngine:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.speaking = False
        self.current_text = None
        self.is_windows = platform.system() == "Windows"
        
        # Thread-safe queue for TTS requests
        self.queue = queue.Queue()
        
        # Start the dedicated TTS worker thread
        self.worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.worker_thread.start()
        print("[TTS] Queue worker thread started")

    def _tts_worker(self):
        if self.is_windows:
            self._windows_tts_worker()
        else:
            self._pyttsx3_tts_worker()
            
    def _windows_tts_worker(self):
        """Dedicated Windows SAPI worker that uses win32com for instantaneous interruption"""
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Optional: Find Zira or David 
            # for voice in speaker.GetVoices():
            #     if "Zira" in voice.GetDescription():
            #         speaker.Voice = voice
            #         break

            print("[TTS Worker] Windows SAPI5 Engine initialized successfully")
        except Exception as e:
            print(f"[TTS Worker Error] Could not initialize Windows SAPI: {e}")
            return
            
        while True:
            item = self.queue.get()
            
            if item == "<STOP>":
                speaker.Speak("", 2) # SVSFPurgeBeforeSpeak
                self.speaking = False
                self.current_text = None
                self.queue.task_done()
                continue
                
            if not self.enabled:
                self.queue.task_done()
                continue
                
            # Start speaking async with purge
            self.speaking = True
            self.current_text = item
            # 3 = SVSFlagsAsync (1) | SVSFPurgeBeforeSpeak (2)
            speaker.Speak(item, 3)
            
            # Wait loop to process interrupts instantly
            while True:
                try:
                    next_item = self.queue.get_nowait()
                    if next_item == "<STOP>":
                        speaker.Speak("", 2)
                        self.speaking = False
                        self.current_text = None
                        self.queue.task_done()
                        break
                    else:
                        speaker.Speak(next_item, 3)
                        self.current_text = next_item
                        self.queue.task_done()
                except queue.Empty:
                    pass
                
                # Check if speaking finished
                if speaker.WaitUntilDone(100):
                    self.speaking = False
                    self.current_text = None
                    break

            self.queue.task_done()

    def _pyttsx3_tts_worker(self):
        """Standard pyttsx3 worker for Mac/Linux"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 170)
            engine.setProperty('volume', 1.0)
            
            def on_start(name): pass
            def on_word(name, location, length):
                if getattr(self, '_stop_requested', False):
                    engine.stop()
            def on_end(name, completed):
                self.speaking = False
                self.current_text = None
                
            engine.connect('started-utterance', on_start)
            engine.connect('started-word', on_word)
            engine.connect('finished-utterance', on_end)
            
            while True:
                item = self.queue.get()
                
                if item == "<STOP>":
                    if self.speaking:
                        engine.stop()
                    self.speaking = False
                    self.current_text = None
                    self.queue.task_done()
                    continue
                    
                self.speaking = True
                self.current_text = item
                self._stop_requested = False
                try:
                    engine.say(item)
                    engine.runAndWait()
                except Exception as e:
                    print(f"[TTS Worker Error] {e}")
                finally:
                    self.speaking = False
                    self.current_text = None
                    self._stop_requested = False
                    self.queue.task_done()
        except Exception as e:
            print(f"[TTS Worker Fatal Error] {e}")

    def _clean_text(self, text):
        if not text:
            return ""
        clean_text = text.replace('###', '').replace('#', '')
        # Remove emojis
        import re
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE)
        clean_text = emoji_pattern.sub('', clean_text)
        return re.sub(r'\s+', ' ', clean_text).strip()
    
    def speak(self, text, wait=False):
        """Convert text to speech async by placing it on the queue."""
        if not self.enabled or not text:
            return
        
        clean_text = self._clean_text(text)
        if len(clean_text) < 3:
            return
            
        print(f"[TTS] Enqueueing speech: {clean_text[:100]}...")
        self.queue.put(clean_text)
        
        if wait:
            self.queue.join()
            
    def toggle_speak(self, text):
        """Toggle TTS: if speaking same text, stop; otherwise stop current and start new"""
        clean_text = self._clean_text(text)
        if len(clean_text) < 3:
            return
        
        # If currently speaking the exact same text, stop it
        if self.speaking and self.current_text == clean_text:
            print(f"[TTS] Stopping current speech")
            self.stop()
            return

        # If speaking different text, stop whatever is playing first
        if self.speaking:
            print(f"[TTS] Switching to new text")
            self.stop()
            time.sleep(0.05)

        # Enqueue new text
        self.speak(text)
    
    def toggle(self):
        """Toggle TTS on/off"""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop()
        status = "ENABLED" if self.enabled else "DISABLED"
        print(f"[TTS] TTS {status}")
        return self.enabled
    
    def stop(self):
        """Stop any ongoing speech by clearing the queue and sending a STOP signal"""
        print("[TTS] Send STOP signal")
        self._stop_requested = True
        
        # Empty any pending utterances
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break
                
        # Send stop command to interrupt active engine.runAndWait()
        self.queue.put("<STOP>")

# Global TTS instance
tts = TTSEngine()

# Test function
if __name__ == "__main__":
    print("Testing TTS Queue Worker...")
    tts.speak("PriVox AI Assistant is ready. Testing one two three.")
    time.sleep(1)
    tts.stop()
    tts.speak("We just aborted the previous sentence to say this one.")
    time.sleep(3)
    print("Test complete!")