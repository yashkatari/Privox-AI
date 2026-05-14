import threading
import time

class AssistantState:
    def __init__(self):
        self.lock = threading.Lock()
        self.allow_listening = True
        self.llm_generating = False
        self.manual_stop = False
        self.last_llm_end_time = 0
        self.cooldown_seconds = 2.0  # 2 second cooldown after LLM

    def can_listen(self):
        with self.lock:
            # Check if we're in cooldown period after LLM
            if time.time() - self.last_llm_end_time < self.cooldown_seconds:
                return False
            return self.allow_listening and not self.llm_generating and not self.manual_stop

    def start_listening(self):
        with self.lock:
            self.allow_listening = True
            self.manual_stop = False

    def stop_listening(self):
        with self.lock:
            self.allow_listening = False

    def llm_start(self):
        with self.lock:
            self.llm_generating = True
            self.allow_listening = False

    def llm_stop(self):
        with self.lock:
            self.llm_generating = False
            self.allow_listening = True
            self.last_llm_end_time = time.time()  # Set cooldown timestamp

    def manual_stop_triggered(self):
        with self.lock:
            self.manual_stop = True
            self.allow_listening = False


# 🔥 GLOBAL INSTANCE (IMPORTANT)
assistant_state = AssistantState()
