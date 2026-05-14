"""
Debug TTS issues
"""
import sys
import os
sys.path.append('.')

print("=== TTS DEBUG SCRIPT ===")

# Test the text cleaning
sample_text = "It seems like you might be referring to an 'Ai' in the context of a manual or guide for artificial intelligence systems. If that's the case, I'd be happy to help explain key aspects of AI and its applications."

print(f"\n1. Sample text: {sample_text[:100]}...")
print(f"   Length: {len(sample_text)}")

# Test cleaning
from tts.windows_tts import WindowsTTS
tts = WindowsTTS()

cleaned = tts._clean_text(sample_text)
print(f"\n2. Cleaned text: {cleaned[:100]}...")
print(f"   Length: {len(cleaned)}")

# Test speaking
print("\n3. Testing TTS speak...")
tts.speak(sample_text, wait=True)

print("\n✅ Debug complete!")