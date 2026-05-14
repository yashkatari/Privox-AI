import sys
import os
sys.path.append('.')

print("=== DIAGNOSTIC ===")

# 1. Check TTS
print("\n1. Checking TTS...")
from tts.speaker import tts
print(f"TTS enabled: {tts.enabled}")
print(f"TTS engine: {tts.engine}")

# 2. Check Smart Features
print("\n2. Checking Smart Features...")
from system.smart_features import smart_features
response = smart_features.get_smart_response("hello")
print(f"Hello response: {response}")

# 3. Check System Commands
print("\n3. Checking System Commands...")
from system.light_commands import enhanced_system_commands as system_commands
success, result = system_commands.execute_command("open youtube")
print(f"Open YouTube: Success={success}, Result={result}")

print("\n✅ Diagnostic complete!")