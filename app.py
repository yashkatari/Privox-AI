import time
import sys
import threading
import subprocess
import os
from pathlib import Path
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask import copy_current_request_context
import logging

# --- Import Your Code ---
from wakeword.detector import start_wakeword_detection
from stt.streaming_whisper import start_stt, stop_stt
from llm.qwen_local import QwenLLM
from llm.offline_llm import OfflineLLM
from tts.speaker import tts as tts_engine
from system.light_commands import enhanced_system_commands as system_commands
from system.smart_features import smart_features
from system.gemini_online import GeminiClient, should_use_gemini
from system.openrouter import OpenRouterClient
from system.openai_client import OpenAIClient
from utils.web_scraper import get_live_info
from system.groq_client import generate as groq_generate
from encryption import SimpleE2EEncryption
from assistant_state import assistant_state
from system.vision_engine import vision_engine
from system.automation_engine import automation_engine
from system.knowledge_vault import knowledge_vault

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

def load_env_file(path=".env"):
    """Lightweight .env loader (no external deps)."""
    try:
        if not Path(path).exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"[Env] Failed to load {path}: {e}")

load_env_file()
e2e_encryption = SimpleE2EEncryption()
print(f"[E2E] Encryption initialized. Fingerprint: {e2e_encryption.get_public_key_fingerprint()}")
gemini_client = GeminiClient.from_env()
if gemini_client.is_configured():
    print("[Gemini] Online API configured.")
else:
    print("[Gemini] Online API not configured. Set GEMINI_API_KEY and GEMINI_API_URL to enable.")
openrouter_client = OpenRouterClient.from_env()
if openrouter_client.is_configured():
    print("[OpenRouter] Online API configured.")
else:
    print("[OpenRouter] Online API not configured. Set OPENROUTER_API_KEY to enable.")
openai_client = OpenAIClient.from_env()
if openai_client.is_configured():
    print("[OpenAI] API configured as fallback.")
else:
    print("[OpenAI] API not configured. Set OPENAI_API_KEY to enable optional fallback.")

# Use when saving data
# --- Configuration ---
LLM_MODEL_NAME = "qwen2.5:3b"
OFFLINE_MODEL_NAME = "tinyllama"
PROMPT_FILE = Path("llm/prompts/main_prompt.txt")

# --- Global State Management ---
llm_engine = None
offline_llm_engine = None
main_system_prompt = ""
is_online_mode = True
is_generating = False
stop_generation_flag = threading.Event()
current_generation_thread = None
tts_enabled = True

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

def load_prompt(file_path):
    """Loads the system prompt from a file."""
    if not file_path.exists():
        print(f"[Warning] Prompt file not found: {file_path}")
        print("[Warning] Using a default system prompt.")
        return "You are PriVox, a helpful, conversational AI voice assistant."
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def process_llm_and_tts(text):
    global is_generating, stop_generation_flag, current_generation_thread
    
    # Set generating flag
    is_generating = True
    assistant_state.llm_start()
    stop_generation_flag.clear()
    
    print(f"[Processing] User said: '{text}'")
    
    # Stop STT while thinking
    try:
        stop_stt()
    except Exception:
        pass
    
    def send_response(response, should_speak=False):

        print(f"[Response] Sending to UI: {response[:50]}...")
        
        # Hide thinking UI
        socketio.emit('hide_thinking_ui')
        
        # Send response to show in chat
        socketio.emit('ai_response', {'text': response})
        print(f"[Response] Sent to chat UI")
        
        # AUTO-TTS FOR ALL RESPONSES WHEN TTS IS ENABLED
        if tts_enabled and response and len(response.strip()) > 5:
            print(f"[TTS] Auto-speaking response...")
            # Clean the response a bit first
            clean_response = response
            # Remove emojis for cleaner speech
            import re
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                "]+", flags=re.UNICODE)
            clean_response = emoji_pattern.sub('', clean_response)
            clean_response = clean_response.strip()
            
            if len(clean_response) > 3:
                print(f"[TTS] Speaking: {clean_response[:50]}...")
                tts_engine.speak(clean_response)
        
        # Removed auto-restart of STT - wait for explicit user intent
        
        global is_generating
        is_generating = False
    
    # ================ SMART FEATURES CHECK ================
    smart_response = smart_features.get_smart_response(text)
    if smart_response:
        print(f"[Smart Feature] Matched: '{text}'")
        send_response(smart_response, should_speak=False)
        return
    
    # ================ EMOTIONAL INTELLIGENCE ================
    emotion_response = smart_features.handle_emotion(text)
    if emotion_response:
        print(f"[Emotion] Matched: '{text}'")
        send_response(emotion_response, should_speak=False)
        return
    
    # ================ WEATHER CHECK ================
    if any(word in text.lower() for word in ["weather", "temperature", "forecast", "how hot", "how cold", "wather"]):
        print(f"[Weather] Checking weather for: '{text}'")
        
        def get_weather_background():
            try:
                weather_response = smart_features.get_weather(text)
                send_response(weather_response, should_speak=False)
            except Exception as e:
                print(f"[Weather Error] {e}")
                send_response("Sorry, I couldn't get the weather right now.", should_speak=False)
        
        threading.Thread(target=get_weather_background, daemon=True).start()
        return
    
    # ================ DAY PLANNER ================
    if any(word in text.lower() for word in ["my day", "day looking", "plan day", "suggestions", "daily"]):
        print(f"[Day Planner] Generating daily suggestions")
        
        def get_day_planner_background():
            try:
                day_response = smart_features.get_daily_suggestions()
                send_response(day_response, should_speak=False)
            except Exception as e:
                print(f"[Day Planner Error] {e}")
                send_response("Sorry, I couldn't generate daily suggestions.", should_speak=False)
        
        threading.Thread(target=get_day_planner_background, daemon=True).start()
        return
    
    # ================ SMART YOUTUBE ================
    if any(word in text.lower() for word in ["play", "youtube", "video", "watch", "music"]):
        print(f"[YouTube] Smart search: '{text}'")
        
        def youtube_search_background():
            try:
                youtube_response = smart_features.smart_youtube_search(text)
                youtube_response = f"🎵 {youtube_response}"
                send_response(youtube_response, should_speak=True)  # SPEAK!
            except Exception as e:
                print(f"[YouTube Error] {e}")
                send_response("Sorry, I couldn't search YouTube.", should_speak=False)
        
        threading.Thread(target=youtube_search_background, daemon=True).start()
        return
    
    # ================ SYSTEM COMMANDS CHECK ================
    success, result = system_commands.execute_command(text)
    
    if success:
        print(f"[System Command] Executing: '{text}'")
        print(f"[System Command] Result: {result}")
        
        # Add visual feedback with emojis
        if "open" in text.lower() and "youtube" in text.lower():
            result = f"🎵 Opening YouTube..."
        elif "open" in text.lower() and "whatsapp" in text.lower():
            result = f"📱 Opening WhatsApp..."
        elif "open" in text.lower() and "calculator" in text.lower():
            result = f"🧮 Opening Calculator..."
        elif "open" in text.lower():
            result = f"🚀 Opening {text.replace('open', '').strip()}"
        elif "screenshot" in text.lower():
            result = f"📸 {result}"
        elif "lock" in text.lower():
            result = f"🔒 {result}"
        elif "terminal" in text.lower() or "cmd" in text.lower():
            result = f"💻 {result}"
        elif "file" in text.lower():
            result = f"📁 {result}"
        
        # Send with auto-TTS for commands
        send_response(result, should_speak=True)
        return
    
    # ================ END SMART/SYSTEM COMMANDS ================
    
    # If not handled above, proceed with LLM
    # In the process_llm_and_tts function, update the LLM section:

# ... [smart features and system commands code] ...

    # ================ VISION ENGINE (SCREEN AWARENESS) ================
    vision_triggers = ["screenshot", "look at my screen", "explain this image", "analyze this picture", "what is on my screen"]
    if any(trigger in text.lower() for trigger in vision_triggers):
        print(f"[Vision] Triggered: '{text}'")
        
        def process_vision_background():
            send_response("👀 Give me a second, I'm analyzing your screen...", should_speak=False)
            img_b64, mime_type = vision_engine.capture_screenshot()
            
            if img_b64:
                # Remove the trigger word from the prompt to get the actual question
                prompt = text
                for t in vision_triggers:
                    prompt = prompt.lower().replace(t, "").strip()
                if not prompt or prompt == "this":
                    prompt = "Explain what is visible in this image in detail."
                
                print(f"[Vision] Passing prompt to Gemini: '{prompt}'")
                vision_result = vision_engine.analyze_image(prompt, img_b64, mime_type)
                send_response(f"📸 **Screen Analysis:**\n{vision_result}", should_speak=True)
            else:
                send_response("❌ Sorry, I failed to capture the screen. Are pyautogui and Pillow installed?", should_speak=True)

        threading.Thread(target=process_vision_background, daemon=True).start()
        return

    # ================ CONTEXT AUTOMATION ENGINE ================
    if "if " in text.lower() and ("battery" in text.lower() or "time" in text.lower()):
        print(f"[Automation] Parsing rule: '{text}'")
        success, msg = automation_engine.add_rule_from_text(text)
        if success:
            send_response(f"⚙️ {msg}", should_speak=True)
            return

    # ================ PERSONAL KNOWLEDGE VAULT ================
    # 1. Save fact
    if any(phrase in text.lower() for phrase in ["remember that", "remember", "save my", "keep in mind"]):
        success, msg = knowledge_vault.remember(text)
        if success:
            send_response(f"🔐 {msg}", should_speak=True)
            return
            
    # 2. Recall fact
    if any(phrase in text.lower() for phrase in ["what is my", "what was my", "do you remember"]):
        success, msg = knowledge_vault.recall(text)
        if success:
            send_response(f"🧠 {msg}", should_speak=True)
            return

    # ================ PROCEED WITH LLM ================
    print(f"[LLM] Proceeding with LLM for: '{text}'")
    print(f"[DEBUG] is_online_mode={is_online_mode}, gemini_configured={gemini_client.is_configured()}, openrouter_configured={openrouter_client.is_configured()}, openai_configured={openai_client.is_configured()}")

    # ================ SIMPLE ONLINE ROUTING (webscrape -> Groq -> Qwen) ================
    if is_online_mode:
        # 1) Try fast web scraping for live data
        try:
            web_result = get_live_info(text)
        except Exception as e:
            web_result = None

        if web_result:
            print(f"\n{'='*60}")
            print(f"✅ WEBSCRAPER ANSWER")
            print(f"Source: Live web scraping")
            print(f"{'='*60}\n")
            send_response(web_result, should_speak=False)
            return

        # 1.5) Try OpenRouter with AES Encryption (Privacy First)
        # Setting key globally (Replaced hardcoded key for GitHub security)
        os.environ["OPENROUTER_API_KEY"] = os.environ.get("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY_HERE")
        openrouter_client.api_key = os.environ["OPENROUTER_API_KEY"]
        
        print(f"[Privacy] Encrypting text before sending to OpenRouter to prevent data leakage...")
        encrypted_text = e2e_encryption.encrypt_data(text)
        print(f"[Privacy] Encrypted snippet: {encrypted_text[:30]}...")
        
        print(f"[LLM] Calling OpenRouter with AES encrypted data...")
        # Note: We are sending the AES encrypted text to OpenRouter as requested to protect privacy
        openrouter_resp, err = openrouter_client.generate_response(encrypted_text, main_system_prompt)
        
        if openrouter_resp and str(openrouter_resp).strip():
            print(f"\n{'='*60}")
            print(f"✅ OPENROUTER ANSWER")
            print(f"Source: OpenRouter API (AES Encrypted Payload)")
            print(f"{'='*60}\n")
            
            # Send the OpenRouter response back to the UI
            send_response(openrouter_resp, should_speak=False)
            return
        
        # 2) Try Groq
        print(f"[LLM] Calling Groq for: '{text}'")
        groq_resp = groq_generate(text, main_system_prompt)
        print(f"[LLM] Groq response received: {repr(groq_resp[:50] if groq_resp else 'EMPTY')}")
        if groq_resp and str(groq_resp).strip():
            print(f"\n{'='*60}")
            print(f"✅ GROQ ANSWER")
            print(f"Source: Groq API")
            print(f"{'='*60}\n")
            send_response(groq_resp, should_speak=False)
            return

        # 3) Fall back to Qwen local LLM
        print("[LLM] Groq unavailable or empty → Using Qwen Local LLM")
    else:
        print("[LLM] Offline mode → Using Offline LLM")

    # Determine source for logging
    source_name = "Qwen" if is_online_mode else "Offline LLM"
    
    # Stream the response
    full_response = ""
    engine = llm_engine if is_online_mode else offline_llm_engine
    
    # Show thinking UI in frontend
    socketio.emit('show_thinking_ui')
    
    try:
        for chunk in engine.generate_response(text, main_system_prompt, stream=True):
            if stop_generation_flag.is_set():
                print("[LLM] Generation stopped by user")
                socketio.emit('generation_stopped', {'text': "*Generating response stopped*"})
                break
            
            full_response += chunk
            socketio.emit('ai_response_partial', {'text': chunk})
        
        print(f"\n{'='*60}")
        print(f"✅ {source_name.upper()} ANSWER")
        print(f"Source: {source_name} Local LLM")
        print(f"{'='*60}")
        print(f"[PRIVVOX] >>> {full_response}")
        
        # Hide thinking UI
        socketio.emit('hide_thinking_ui')
        
        # Send final response
        socketio.emit('ai_response', {'text': full_response})
        
        # IMPORTANT: Auto-TTS for LLM responses too (optional)
        # Uncomment if you want ALL LLM responses to be spoken automatically
        # if tts_enabled and full_response and len(full_response.strip()) > 10:
        #     print("[TTS] Auto-speaking LLM response...")
        #     threading.Thread(target=speak_text, args=(full_response,), daemon=True).start()
        
        # Restart STT after delay
        if not text.startswith("[MANUAL]"):
            threading.Timer(1.0, lambda: start_stt(
                final_callback=handle_final_transcript_socket,
                on_stop_callback=go_back_to_wakeword
            )).start()
        
    except Exception as e:
        print(f"[LLM Error] {e}")
        error_msg = "I encountered an error. Please try again."
        socketio.emit('hide_thinking_ui')
        socketio.emit('ai_response', {'text': error_msg})
        
        # Removed auto-restart of STT - wait for explicit user intent
    
    finally:
        is_generating = False
        assistant_state.llm_stop()
        assistant_state.start_listening()

# --- STT Callback ---
def handle_final_transcript_socket(text):
    # Filter out very short speech or non-intent utterances
    if not text or len(text.strip()) < 5:
        print(f"[STT] Filtered short speech: '{text}'")
        return
    
    # Filter out common non-intent speech patterns
    non_intent_patterns = [
        "uh", "um", "hmm", "ah", "er", "like", "you know", 
        "so", "well", "okay", "alright", "yeah", "yes", "no",
        "hi", "hello", "hey", "bye", "goodbye", "thanks", "thank you"
    ]
    
    text_lower = text.lower().strip()
    if any(pattern in text_lower for pattern in non_intent_patterns) and len(text.strip()) < 10:
        print(f"[STT] Filtered non-intent speech: '{text}'")
        return
    
    global is_generating
    
    print("\n" + "="*30)
    print(f"[USER] >>> {text}")
    
    if is_generating:
        print("[Main] Ignoring input while generating")
        socketio.emit('busy_state', {'message': 'Please wait for current response to complete'})
        return
    
    # Show user message in chat FIRST
    socketio.emit('user_speech', {'text': text})
    
    # Show thinking UI
    socketio.emit('show_thinking_ui')
    
    try:
        stop_stt()
    except Exception:
        pass
    
    # Process in background thread
    llm_thread = threading.Thread(target=process_llm_and_tts, args=(text,), daemon=True)
    llm_thread.start()
    
    if any(cmd in text.lower() for cmd in ["goodbye", "stop listening", "exit", "quit"]):
        print("[Main] Exit command detected. Stopping...")
        socketio.emit('full_stop_ack')

# --- Callback after STT stops ---
def go_back_to_wakeword():
    print("[Main] STT has confirmed stop.")
    socketio.emit('stt_fully_stopped')
    
    # Auto-restart STT after a longer delay to allow cooldown
    # This gives time for LLM response and prevents echo loops
    def delayed_restart():
        time.sleep(3)  # 3 second delay
        if assistant_state.can_listen():  # Double-check cooldown
            print("[Main] Auto-restarting STT after cooldown...")
            start_stt(final_callback=handle_final_transcript_socket, on_stop_callback=go_back_to_wakeword)
    
    threading.Thread(target=delayed_restart, daemon=True).start()

# --- Flask Routes & SocketIO Events ---
@app.route('/')
def index():
    return render_template('index.html')
# Add to your existing socket handlers in app.py

@socketio.on('encrypt_data')
def handle_encrypt_data(data):
    """Encrypt data sent from frontend"""
    try:
        print(f"[E2E] Encrypting data of length: {len(str(data.get('data', '')))}")
        
        # Encrypt the data
        encrypted = e2e_encryption.encrypt_data(data.get('data'))
        
        emit('encryption_complete', {
            'encrypted': encrypted,
            'fingerprint': e2e_encryption.get_public_key_fingerprint()
        })
        
    except Exception as e:
        print(f"[E2E Error] {e}")
        emit('encryption_error', {'error': str(e)})

@socketio.on('decrypt_data')
def handle_decrypt_data(data):
    """Decrypt data sent from frontend"""
    try:
        print(f"[E2E] Decrypting data")
        
        # Decrypt the data
        decrypted = e2e_encryption.decrypt_data(data.get('encrypted'))
        
        emit('decryption_complete', {
            'decrypted': decrypted
        })
        
    except Exception as e:
        print(f"[E2E Error] {e}")
        emit('encryption_error', {'error': str(e)})

@socketio.on('get_encryption_info')
def handle_get_encryption_info():
    """Send encryption fingerprint to frontend"""
    emit('encryption_info', {
        'fingerprint': e2e_encryption.get_public_key_fingerprint(),
        'status': 'active'
    })
@socketio.on('start_wakeword')
def on_start_wakeword():
    print("[SocketIO] Starting wakeword detection...")
    try:
        # Start wakeword detection (blocking until detected)
        wakeword_detected = start_wakeword_detection()
        if wakeword_detected:
            emit('wakeword_detected', {'triggered': True})
            start_stt(
                final_callback=handle_final_transcript_socket,
                on_stop_callback=go_back_to_wakeword
            )
        else:
            emit('wakeword_detected', {'triggered': False})
    except Exception as e:
        print(f"[SocketIO] Wakeword detection error: {e}")
        emit('wakeword_detected', {'triggered': False})

@socketio.on('hide_thinking_ui')
def on_hide_thinking_ui():
    """Hide the thinking UI"""
    print("[SocketIO] Hiding thinking UI")
    emit('hide_thinking_ui')

@socketio.on('toggle_online_mode')
def on_toggle_online_mode(data):
    global is_online_mode
    is_online_mode = data.get('online', True)
    mode = "ONLINE" if is_online_mode else "OFFLINE"
    print(f"[SocketIO] Switched to {mode} mode")
    emit('mode_changed', {'online': is_online_mode, 'message': f"Switched to {mode} mode"})

@socketio.on('toggle_tts')
def on_toggle_tts(data):
    global tts_enabled
    tts_enabled = data.get('enabled', True)
    status = "ENABLED" if tts_enabled else "DISABLED"
    print(f"[SocketIO] TTS {status}")
    emit('tts_status', {'enabled': tts_enabled, 'message': f"TTS {status}"})

@socketio.on('hard_stop')
def on_hard_stop():
    global stop_generation_flag, is_generating
    
    print("[SocketIO] HARD STOP requested")
    
    # Stop STT and generation, but NOT TTS
    try:
        stop_stt()
    except:
        pass
    
    stop_generation_flag.set()
    is_generating = False
    assistant_state.manual_stop_triggered()
    assistant_state.llm_stop()
    
    socketio.emit('generation_stopped', {'text': "*Generating response stopped*"})
    socketio.emit('reset_state')
    
    print("[SocketIO] Generation stopped (TTS not affected)")

@socketio.on('stop_stt')
def on_stop_stt():
    print("[SocketIO] Stop STT requested")
    stop_stt()
    assistant_state.stop_listening()
    emit('stt_stopped')

@socketio.on('start_stt')
def on_start_stt():
    print("[SocketIO] Start STT requested")
    assistant_state.start_listening()
    start_stt(final_callback=handle_final_transcript_socket, on_stop_callback=go_back_to_wakeword)
    emit('stt_started')

@socketio.on('manual_text')
def on_manual_text(data):
    global is_generating
    
    if is_generating:
        emit('busy_state', {'message': 'Please wait for current response to complete'})
        return
    
    text = data.get('text')
    if text:
        print(f"[SocketIO] Manual text received: {text}")
        
        # Mark as manual to prevent auto-restart of STT
        marked_text = f"[MANUAL] {text}"
        
        # Show user message
        socketio.emit('user_speech', {'text': text})
        
        # Show thinking UI
        socketio.emit('show_thinking_ui')
        
        # Process with MANUAL flag
        threading.Thread(target=process_llm_and_tts, args=(marked_text,), daemon=True).start()

@socketio.on('speak_text')
def handle_speak_text(data):
    """Handle speaker button clicks - FIXED VERSION"""
    text = data.get('text', '').strip()
    
    if len(text) < 10:
        print(f"[TTS] Text too short: '{text}'")
        return
    
    print(f"[TTS Click] Text length: {len(text)}")
    
    # Stop STT if running
    try:
        stop_stt()
        time.sleep(0.1)  # Small delay
    except:
        pass
    
    # Use a fresh thread for TTS
    def speak_in_thread():
        try:
            # Clean the text
            import re
            clean_text = re.sub(r'[^\w\s.,!?\-]', ' ', text[:500])  # Limit length
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            if len(clean_text) > 5:
                print(f"[TTS] Speaking via button: {clean_text[:50]}...")
                tts_engine.toggle_speak(clean_text)
        except Exception as e:
            print(f"[TTS Thread Error] {e}")
    
    # Start in separate thread
    threading.Thread(target=speak_in_thread, daemon=True).start()
    
    # Send feedback
    socketio.emit('tts_started', {'message': 'TTS triggered...'})




# --- Main Initialization ---
if __name__ == "__main__":
    print(f"Loading system prompt from {PROMPT_FILE}")
    main_system_prompt = load_prompt(PROMPT_FILE)
    print("[Main] System prompt loaded.")
    
    print(f"Initializing ONLINE LLM: {LLM_MODEL_NAME}")
    try:
        llm_engine = QwenLLM(LLM_MODEL_NAME)
        print("[Main] Online LLM engine ready.")
    except Exception as e:
        print(f"[Main] Failed to load online LLM: {e}")
        llm_engine = None
    
    print(f"Initializing OFFLINE LLM: {OFFLINE_MODEL_NAME}")
    try:
        offline_llm_engine = OfflineLLM(OFFLINE_MODEL_NAME)
        print("[Main] Offline LLM engine ready.")
    except Exception as e:
        print(f"[Main] Failed to load offline LLM: {e}")
        offline_llm_engine = None
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    
    # Test TTS on startup
    print("[Main] Testing TTS...")
    try:
        tts_engine.speak("AI Assistant is ready.")

        print("[Main] TTS test successful!")
    except Exception as e:
        print(f"[Main] TTS test failed: {e}")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
