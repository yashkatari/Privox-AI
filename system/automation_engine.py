"""
Context Automation Engine for PriVox
Evaluates ambient user conditions (battery, time, context) and triggers actions.
"""
import os
import json
import time
import threading
import datetime
import subprocess
from pathlib import Path
import psutil

try:
    import screen_brightness_control as sbc
except ImportError:
    sbc = None

# A rule looks like: 
# { "condition_type": "battery", "operator": "<", "value": 15, "action": "dim_screen" }
# { "condition_type": "time", "operator": "==", "value": "21:00", "action": "study_mode" }

class AutomationEngine:
    def __init__(self):
        self.rules_file = Path("data/automation_rules.json")
        self.rules = []
        self._load_rules()
        self.running = True
        self.last_triggered = {}
        
        # Start the background evaluator
        self.eval_thread = threading.Thread(target=self._evaluation_loop, daemon=True)
        self.eval_thread.start()

    def _load_rules(self):
        self.rules_file.parent.mkdir(exist_ok=True)
        if self.rules_file.exists():
            try:
                with open(self.rules_file, "r") as f:
                    self.rules = json.load(f)
            except Exception as e:
                print(f"[Automation Error] Failed to load rules: {e}")
                self.rules = []
        else:
            # Default starting rules
            self.rules = []
            self._save_rules()

    def _save_rules(self):
        with open(self.rules_file, "w") as f:
            json.dump(self.rules, f, indent=4)

    def add_rule_from_text(self, text):
        """
        Parses user intent: "if battery is less than 20% turn on power saver"
        Returns True and confirmation message, or False if parser fails.
        """
        text = text.lower()
        if "if" not in text:
            return False, ""
            
        # VERY basic heuristics. In a full production system, we'd feed this to the local LLM to output a JSON rule.
        condition_type = None
        operator = None
        value = None
        action = None
        
        # 1. Detect Condition
        if "battery" in text:
            condition_type = "battery"
            import re
            nums = re.findall(r'\d+', text)
            if nums:
                value = int(nums[0])
            if "less" in text or "<" in text:
                operator = "<"
            elif "greater" in text or ">" in text:
                operator = ">"
            elif "equal" in text or "is" in text:
                operator = "=="
                
        elif "time" in text:
            condition_type = "time"
            import re
            # look for something like "9 pm" or "21:00"
            matches = re.findall(r'(\d{1,2})(?::\d{2})?\s*(am|pm)?', text)
            if matches:
                hour = int(matches[0][0])
                ampm = matches[0][1]
                if ampm == 'pm' and hour < 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0
                value = f"{hour:02d}:00"
                operator = "=="
                
        # 2. Detect Action
        if "dim screen" in text or "reduce brightness" in text:
            action = "dim_screen"
        elif "study mode" in text or "focus mode" in text:
            action = "study_mode"
        elif "silent" in text or "mute" in text:
            action = "mute_audio"
            
        if condition_type and operator and value is not None and action:
            new_rule = {
                "id": str(int(time.time())),
                "condition_type": condition_type,
                "operator": operator,
                "value": value,
                "action": action
            }
            self.rules.append(new_rule)
            self._save_rules()
            human_readable = f"If {condition_type} {operator} {value}, then {action}."
            return True, f"Automation saved: {human_readable}"
            
        return False, ""

    def _evaluation_loop(self):
        """Continuously polls the rules against system state."""
        while self.running:
            try:
                self._evaluate_rules()
            except Exception as e:
                print(f"[Automation Error] {e}")
            time.sleep(60) # Poll every 1 minute

    def _evaluate_rules(self):
        battery_pct = None
        if hasattr(psutil, "sensors_battery"):
            bat = psutil.sensors_battery()
            if bat: battery_pct = bat.percent
            
        now_str = datetime.datetime.now().strftime("%H:%M")
        
        for rule in self.rules:
            rule_id = rule.get("id")
            # Don't trigger the same rule more than once an hour
            if rule_id in self.last_triggered:
                if (time.time() - self.last_triggered[rule_id]) < 3600:
                    continue
                    
            condition = rule.get("condition_type")
            operator = rule.get("operator")
            target_val = rule.get("value")
            action = rule.get("action")
            
            triggered = False
            
            if condition == "battery" and battery_pct is not None:
                if operator == "<" and battery_pct < int(target_val):
                    triggered = True
                elif operator == ">" and battery_pct > int(target_val):
                    triggered = True
                elif operator == "==" and battery_pct == int(target_val):
                    triggered = True
                    
            elif condition == "time":
                # Only check hours to avoid 60 second race condition matching
                if operator == "==" and now_str.startswith(str(target_val).split(':')[0]):
                    triggered = True
                    
            if triggered:
                print(f"[Automation Triggered] Rule {rule_id}: {condition} {operator} {target_val}")
                self._execute_action(action)
                self.last_triggered[rule_id] = time.time()

    def _execute_action(self, action):
        if action == "dim_screen":
            if sbc:
                sbc.set_brightness(20)
                from tts.speaker import tts
                tts.speak("Automation triggered. Dimming the screen.")
            else:
                print("[Automation Error] screen-brightness-control not installed")
                
        elif action == "mute_audio":
            # Windows native mute
            import platform
            if platform.system() == "Windows":
                # simple powershell media key pressing
                ps_script = '$obj = new-object -com wscript.shell; $obj.SendKeys([char]173)'
                subprocess.Popen(["powershell", "-Command", ps_script])
                
        elif action == "study_mode":
            # Example study mode: dim screen slightly, open notepad or calendar
            if sbc: sbc.set_brightness(50)
            subprocess.Popen(["notepad"])
            from tts.speaker import tts
            tts.speak("Study mode activated. Ambient distractions reduced.")

# Global instance
automation_engine = AutomationEngine()
