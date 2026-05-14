"""
Vision Engine for PriVox AI Assistant
Handles taking screenshots and analyzing them using Google Gemini Vision API.
"""
import os
import base64
import time
import requests
from io import BytesIO

class VisionEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # We need a URL that supports Vision. Gemini 1.5 Flash or Pro supports multimodal.
        # If the environment variable isn't specifically the generateContent URL, we'll try to use a default.
        custom_url = os.getenv("GEMINI_API_URL", "")
        if "gemini-1.5" in custom_url.lower():
            self.api_url = custom_url
        else:
            # Default to gemini-1.5-flash for fast multimodal tasks
            self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def is_configured(self):
        return bool(self.api_key)

    def capture_screenshot(self):
        """Captures a screenshot and returns it as a base64 encoded string & mime type"""
        try:
            import pyautogui
            from PIL import Image
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Convert to RGB (in case it's RGBA)
            if screenshot.mode != 'RGB':
                screenshot = screenshot.convert('RGB')
                
            # Resize a bit to save bandwidth and API limits while maintaining readability
            # Gemini has high limits, but 1080p equivalent is plenty
            max_size = (1920, 1080)
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save to BytesIO
            buffered = BytesIO()
            screenshot.save(buffered, format="JPEG", quality=85)
            
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            return img_str, "image/jpeg"
        except ImportError:
            print("[Vision] Error: pyautogui or Pillow not installed. Install with `pip install pyautogui pillow`")
            return None, None
        except Exception as e:
            print(f"[Vision] Screenshot error: {e}")
            return None, None

    def analyze_image(self, prompt, base64_img, mime_type="image/jpeg"):
        """Sends the prompt and image to Gemini Vision API"""
        if not self.is_configured():
            return "Gemini API is not configured. Please set GEMINI_API_KEY in your .env file to use Screen Awareness."
            
        if not base64_img:
            return "Failed to capture the screen. Are the required packages installed?"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_img
                            }
                        }
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        print("[Vision] Sending screenshot to Gemini Vision API...")
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text_out.strip()
                except (KeyError, IndexError):
                    print(f"[Vision Error] Unexpected response format: {data}")
                    return "Sorry, I received an invalid response from the vision model."
            else:
                print(f"[Vision Error] HTTP {response.status_code}: {response.text}")
                return "Sorry, the vision model failed to process the image."
                
        except Exception as e:
            print(f"[Vision Request Error] {e}")
            return f"An error occurred while connecting to the vision model: {e}"

# Global instance
vision_engine = VisionEngine()
