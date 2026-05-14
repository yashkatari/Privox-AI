import sounddevice as sd
import numpy as np
import threading
import time
import queue
import collections
import whisper

from stt.vad import SileroVAD
from assistant_state import assistant_state

# ================= CONFIG =================

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK = 1024

ENERGY_THRESHOLD = 0.005
SILENCE_TIMEOUT =1.2         # human-safe pause
MIN_SPEECH_SAMPLES = int(0.3 * SAMPLE_RATE)

MAX_SPEECH_SECONDS = 8
MAX_SPEECH_SAMPLES = SAMPLE_RATE * MAX_SPEECH_SECONDS

# ==========================================

print("Loading Whisper model...")
model = whisper.load_model("medium")
print("Whisper loaded")

vad = SileroVAD()
print("Silero VAD ready")


class StreamingSTT:
    def __init__(self, final_callback=None, on_stop_callback=None):
        self.final_callback = final_callback
        self.on_stop_callback = on_stop_callback

        self.listening = False
        self.is_speaking = False
        self.finalized = False
        self.stopping = False

        self.last_voice_time = 0

        self.audio_queue = queue.Queue()
        self.speech_buffer = collections.deque()

        self.buffered_samples = 0

        self.stream = None
        self.processing_thread = None
        self.monitor_thread = None

        self._stop_event = threading.Event()
        self.finalize_lock = threading.Lock()
        self.finalizing = False  # 🔥 NEW: Block mic during finalize

    # -------- AUDIO CALLBACK --------

    def _callback(self, indata, frames, time_info, status):
        if self.finalizing:  # 🔥 HARD BLOCK mic during finalize
            return
        if status:
            print("[Audio warning]", status)
        self.audio_queue.put(indata[:, 0].copy().astype(np.float32))

    # -------- MAIN AUDIO LOOP --------

    def _process_audio_queue(self):
        while not self._stop_event.is_set():
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)

                # rms = np.sqrt(np.mean(audio_chunk ** 2))
                # is_speech_chunk = False

                # if rms > ENERGY_THRESHOLD:
                #     is_speech_chunk = vad.is_speech(audio_chunk)
                is_speech_chunk = vad.is_speech(audio_chunk)


                # ---- SPEECH START ----
                if is_speech_chunk:
                    self.last_voice_time = time.time()

                    if not self.is_speaking:
                        print("[STT] Speech started")

                        # 🔥 Move VAD buffered audio into STT buffer
                        if hasattr(vad, "vad_buffer") and vad.vad_buffer:
                            for chunk in vad.vad_buffer:
                                self.speech_buffer.append(chunk)
                                self.buffered_samples += len(chunk)

                        self.is_speaking = True

                # ---- BUFFER AUDIO ----
                if self.is_speaking and not self.finalized:
                    self.speech_buffer.append(audio_chunk)
                    self.buffered_samples += len(audio_chunk)

                    # ---- HARD LIMIT ----
                    if self.buffered_samples >= MAX_SPEECH_SAMPLES:
                        print(f"[STT] Max speech length ({MAX_SPEECH_SECONDS}s) reached")
                        self._finalize()
                        continue

                    # ---- STREAM PARTIAL TEXT ----
                    self._stream_partial()

            except queue.Empty:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    print("[STT Process Error]", e)

    # -------- SILENCE MONITOR --------

    def _silence_monitor(self):
        while not self._stop_event.is_set():
            if not assistant_state.can_listen():
                print("[STT] Stopping due to state")
                self._finalize()
                break
            time.sleep(0.1)

            # 🔥 Do NOT allow early finalize
            if self.buffered_samples < SAMPLE_RATE * 0.8:
                continue

            if self.is_speaking and not self.finalized:
                if time.time() - self.last_voice_time > SILENCE_TIMEOUT:
                    print("[STT] Silence detected")
                    self._finalize()

    # -------- STREAM PARTIAL TEXT --------

    def _stream_partial(self):
        try:
            if not self.is_speaking or self.finalized:
                return

            if len(self.speech_buffer) < 4:
                return

            audio = np.concatenate(list(self.speech_buffer)[-6:])
            if len(audio) < SAMPLE_RATE:
                return

            result = model.transcribe(
                audio,
                language="en",
                fp16=False
            )

            partial = result["text"].strip()
            if partial:
                print(f"[STT STREAM] {partial}")

        except Exception:
            pass

    # -------- FINALIZE --------

    def _finalize(self):
        if self.stopping or self.finalized or self.finalizing:
            return

        self.finalizing = True  # 🔒 HARD FREEZE MIC + VAD
        print("[STT] Finalizing - mic blocked")

        self.is_speaking = False  # 🔥 STOP BUFFERING IMMEDIATELY

        with self.finalize_lock:
            if self.finalized:
                return
            self.finalized = True

            if not self.speech_buffer:
                return

            audio = np.concatenate(list(self.speech_buffer)).astype(np.float32)
            self.speech_buffer.clear()
            self.buffered_samples = 0

        if len(audio) < MIN_SPEECH_SAMPLES:
            print("[STT] Audio too short")
            self.stop()
            return

        print(f"[STT] Transcribing {len(audio) / SAMPLE_RATE:.2f}s audio")

        try:
            result = model.transcribe(
                audio,
                language="en",
                fp16=False
            )

            text = result["text"].strip()
            print(f"[STT FINAL] >>> {text}")

            if text and self.final_callback:
                self.final_callback(text)

        except Exception as e:
            print("[STT Finalize Error]", e)

        finally:
            self.finalizing = False  # 🔓 UNLOCK MIC
            print("[STT] Finalize complete - mic unblocked")

        self.stop()

    # -------- START --------

    def start(self):
        if not assistant_state.can_listen():
            print("[STT] Cannot start listening due to state")
            return

        if self.listening:
            return

        self.finalized = False
        self.stopping = False
        self.is_speaking = False

        self.speech_buffer.clear()
        self.buffered_samples = 0
        self._stop_event.clear()

        print("[STT] Starting stream")

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=BLOCK,
            callback=self._callback,
            dtype="float32"
        )
        self.stream.start()

        self.processing_thread = threading.Thread(
            target=self._process_audio_queue, daemon=True
        )
        self.processing_thread.start()

        self.monitor_thread = threading.Thread(
            target=self._silence_monitor, daemon=True
        )
        self.monitor_thread.start()

        self.listening = True
        print("[STT] Listening...")

    # -------- STOP --------

    def stop(self):
        if self.stopping:
            return

        self.stopping = True
        print("[STT] Stopping stream")

        self._stop_event.set()

        current = threading.current_thread()

        if self.processing_thread and self.processing_thread != current:
            self.processing_thread.join(timeout=0.5)

        if self.monitor_thread and self.monitor_thread != current:
            self.monitor_thread.join(timeout=0.5)

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
        except Exception:
            pass

        self.listening = False
        self.is_speaking = False

        print("[STT] Stream stopped")

        if self.on_stop_callback:
            self.on_stop_callback()


# -------- GLOBAL ENGINE --------

_engine = None

def start_stt(final_callback=None, on_stop_callback=None):
    global _engine
    
    # Check if we can listen (not during LLM generation or cooldown)
    if not assistant_state.can_listen():
        print("[STT] Cannot start - assistant is busy or in cooldown")
        return None
    
    # 🔥 BLOCK STT if TTS is currently speaking
    from tts.speaker import tts
    if tts.speaking:
        print("[STT] Blocked: TTS is currently speaking")
        return None
    
    if _engine is None:
        _engine = StreamingSTT(final_callback, on_stop_callback)
    else:
        _engine.final_callback = final_callback
        _engine.on_stop_callback = on_stop_callback

    _engine.start()
    return _engine


def stop_stt():
    global _engine
    if _engine:
        _engine.stop()
        _engine = None


def transcribe_file(file_path: str) -> str:
    """Transcribe an audio file to text using the global `model`.

    Uses `soundfile` + `torchaudio` resampling to avoid external ffmpeg dependency.
    Returns the transcription string (empty string on failure).
    """
    # Try multiple loaders: soundfile (wav/flac), torchaudio, pydub (mp3)
    audio = None
    sr = None

    # 1) try soundfile
    try:
        import soundfile as sf
        audio, sr = sf.read(file_path, dtype="float32")
    except Exception:
        audio = None

    # 2) try torchaudio
    if audio is None:
        try:
            import torchaudio
            tensor, sr = torchaudio.load(file_path)
            # tensor shape (channels, samples)
            audio = tensor.numpy()
            if audio.ndim > 1:
                audio = audio.mean(axis=0)
            else:
                audio = audio
        except Exception:
            audio = None

    # 3) try pydub (requires ffmpeg) as last resort
    if audio is None:
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(file_path)
            sr = seg.frame_rate
            samples = seg.get_array_of_samples()
            import numpy as _np
            audio = _np.array(samples).astype("float32") / (1 << (8 * seg.sample_width - 1))
            if seg.channels > 1:
                audio = audio.reshape((-1, seg.channels)).mean(axis=1)
        except Exception as e:
            # Fallback: try ffmpeg CLI to convert mp3 to wav if pydub is not installed
            try:
                import shutil, subprocess, tempfile, os
                # Search for ffmpeg in common Windows locations
                ffmpeg_paths = [
                    shutil.which("ffmpeg"),
                    shutil.which("ffmpeg.exe"),
                    r"C:\Program Files\Krita (x64)\bin\ffmpeg.exe",
                    r"C:\Program Files\BlueStacks_nxt\ffmpeg.exe",
                ]
                ffmpeg = next((p for p in ffmpeg_paths if p and os.path.exists(p)), None)
                if ffmpeg:
                    tmpf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    tmpf.close()
                    cmd = [ffmpeg, "-y", "-i", file_path, "-ar", "16000", "-ac", "1", tmpf.name]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    import soundfile as sf
                    audio, sr = sf.read(tmpf.name, dtype="float32")
                    try:
                        os.unlink(tmpf.name)
                    except Exception:
                        pass
                else:
                    print(f"[transcribe_file Error] mp3 support missing for '{file_path}'; install pydub or ffmpeg")
                    return ""
            except Exception as e2:
                print(f"[transcribe_file Error] Error opening '%s': %s" % (file_path, e2))
                return ""

    # Ensure numpy array and mono
    import numpy as np
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    

    target_sr = 16000
    if sr is None:
        sr = target_sr

    # Resample if needed
    if sr != target_sr:
        try:
            import torch
            import torchaudio.transforms as T
            tensor = torch.from_numpy(audio).unsqueeze(0)
            resampler = T.Resample(sr, target_sr)
            tensor = resampler(tensor)
            audio = tensor.squeeze(0).numpy()
            sr = target_sr
        except Exception as e:
            print("[transcribe_file Error] resample failed:", e)
            return ""

    # Use Silero VAD to extract speech segments if available
    try:
        # `vad` is a module-global instance created at import time
        speech_timestamps = []
        if 'vad' in globals() and hasattr(vad, 'get_speech_timestamps'):
            speech_timestamps = vad.get_speech_timestamps(audio, vad.model, sampling_rate=target_sr)

        if speech_timestamps:
            # Concatenate detected speech segments into one array for cleaner transcription
            segments = []
            for seg in speech_timestamps:
                start = int(seg['start'] * target_sr)
                end = int(seg['end'] * target_sr)
                segments.append(audio[start:end])

            if segments:
                audio = np.concatenate(segments)

    except Exception:
        # If VAD fails, fall back to full audio
        pass

    try:
        result = model.transcribe(audio, language="en", fp16=False)
        return result.get("text", "").strip()
    except Exception as e:
        print("[transcribe_file Error]", e)
        return ""


def load_whisper_model(size: str = "small"):
    """Load and return a Whisper model by size (small, medium, large)."""
    try:
        print(f"[STT] Loading Whisper model: {size}")
        m = whisper.load_model(size)
        print(f"[STT] Whisper model '{size}' loaded")
        return m
    except Exception as e:
        print(f"[STT] Failed to load Whisper model '{size}':", e)
        return None


def transcribe_with_model(file_path: str, model_obj) -> str:
    """Transcribe an audio file using the provided Whisper `model_obj`.

    This duplicates the file-loading/resample + VAD logic from `transcribe_file`
    but targets a specific model instance (so evaluate.py can load larger
    models temporarily without changing the global runtime model).
    """
    if model_obj is None:
        return ""

    # Inline audio loader from transcribe_file
    audio = None
    sr = None

    try:
        import soundfile as sf
        audio, sr = sf.read(file_path, dtype="float32")
    except Exception:
        audio = None

    if audio is None:
        try:
            import torchaudio
            tensor, sr = torchaudio.load(file_path)
            audio = tensor.numpy()
            if audio.ndim > 1:
                audio = audio.mean(axis=0)
        except Exception:
            audio = None

    if audio is None:
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(file_path)
            sr = seg.frame_rate
            samples = seg.get_array_of_samples()
            import numpy as _np
            audio = _np.array(samples).astype("float32") / (1 << (8 * seg.sample_width - 1))
            if seg.channels > 1:
                audio = audio.reshape((-1, seg.channels)).mean(axis=1)
        except Exception:
            # try ffmpeg conversion
            try:
                import shutil, subprocess, tempfile, os
                ffmpeg_paths = [
                    shutil.which("ffmpeg"),
                    shutil.which("ffmpeg.exe"),
                    r"C:\Program Files\Krita (x64)\bin\ffmpeg.exe",
                    r"C:\Program Files\BlueStacks_nxt\ffmpeg.exe",
                ]
                ffmpeg = next((p for p in ffmpeg_paths if p and os.path.exists(p)), None)
                if ffmpeg:
                    tmpf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    tmpf.close()
                    cmd = [ffmpeg, "-y", "-i", file_path, "-ar", "16000", "-ac", "1", tmpf.name]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    import soundfile as sf
                    audio, sr = sf.read(tmpf.name, dtype="float32")
                    try:
                        os.unlink(tmpf.name)
                    except Exception:
                        pass
                else:
                    return ""
            except Exception:
                return ""

    import numpy as np
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    target_sr = 16000
    if sr is None:
        sr = target_sr

    if sr != target_sr:
        try:
            import torch
            import torchaudio.transforms as T
            tensor = torch.from_numpy(audio).unsqueeze(0)
            resampler = T.Resample(sr, target_sr)
            tensor = resampler(tensor)
            audio = tensor.squeeze(0).numpy()
            sr = target_sr
        except Exception:
            return ""

    try:
        # light denoise + normalize before transcription with provided model
        try:
            audio_proc = spectral_denoise(audio, target_sr)
            max_amp = np.max(np.abs(audio_proc)) if audio_proc.size else 1.0
            if max_amp > 0:
                audio_proc = audio_proc / max_amp * 0.95
        except Exception:
            audio_proc = audio

        result = model_obj.transcribe(audio_proc, language="en", fp16=False)
        return result.get("text", "").strip()
    except Exception:
        return ""


def spectral_denoise(audio: np.ndarray, sr: int) -> np.ndarray:
    """Lightweight spectral subtraction denoiser using torch STFT/ISTFT.

    This is intentionally conservative (clamps gain) to avoid artifacts.
    """
    try:
        import torch

        x = torch.from_numpy(audio).float()
        if x.ndim == 2:
            x = x.mean(dim=1)

        n_fft = 1024
        hop = 256
        win = torch.hann_window(n_fft)

        S = torch.stft(x, n_fft=n_fft, hop_length=hop, win_length=n_fft, window=win, return_complex=True)
        mag = S.abs()

        # estimate noise magnitude from first 0.25s (or at least 1 frame)
        frames_per_sec = sr / hop
        noise_frames = max(1, int(0.25 * frames_per_sec))
        if mag.shape[1] < noise_frames:
            noise_frames = mag.shape[1]

        noise_mag = mag[:, :noise_frames].mean(dim=1, keepdim=True)

        # soft spectral subtraction gain
        gain = 1.0 - (noise_mag / (mag + 1e-8))
        gain = torch.clamp(gain, min=0.2, max=1.0)

        S_deno = S * gain

        x_deno = torch.istft(S_deno, n_fft=n_fft, hop_length=hop, win_length=n_fft, window=win, length=x.shape[0])
        out = x_deno.numpy()
        return out
    except Exception:
        return audio
