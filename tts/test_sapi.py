import win32com.client
import pythoncom
import queue
import time

q = queue.Queue()

def worker():
    pythoncom.CoInitialize()
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    
    while True:
        item = q.get()
        if item == "EXIT":
            break
        elif item == "<STOP>":
            speaker.Speak("", 2)
            q.task_done()
            continue
            
        # Speak async and purge
        speaker.Speak(item, 3)
        while True:
            try:
                next_item = q.get_nowait()
                if next_item == "<STOP>":
                    speaker.Speak("", 2)
                    q.task_done()
                    break
                else:
                    speaker.Speak(next_item, 3)
                    q.task_done()
            except queue.Empty:
                pass
            
            if speaker.WaitUntilDone(100):
                break
        q.task_done()

import threading
t = threading.Thread(target=worker)
t.start()

print("Speaking 1...")
q.put("This is a really really really long sentence that should take a long time to read completely.")
time.sleep(1)
print("Sending STOP")
q.put("<STOP>")
time.sleep(1)
print("Speaking 2...")
q.put("This is the new sentence.")
time.sleep(2)
q.put("EXIT")
t.join()
print("Done")
