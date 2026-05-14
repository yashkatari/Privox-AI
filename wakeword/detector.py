import pvporcupine
import pyaudio
import struct
import os
import wave
import soundfile as sf
import torch
import torchaudio.transforms as T

def start_wakeword_detection():
    ACCESS_KEY = "s0QFZ1oBiipJz+2mSNHz1jWPstzR4ExZGDMsiii+tK6XnDddvv5bKQ=="

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[
            os.path.join("wakeword", "models", "hello_privox.ppn")
        ]
    )

    pa = pyaudio.PyAudio()

    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("\n🔊 Listening for Wake Word: 'Hello Pri-vox' (Custom Keyword)")

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)

            if result >= 0:
                print("\n🔥 Wake Word Detected! (HELLO PRIVOX) 🔥\n")
                return True

    finally:
        audio_stream.stop_stream()
        audio_stream.close()
        pa.terminate()
        porcupine.delete()


def detect_wakeword(file_path: str) -> bool:
    """Detects the custom wake word in a WAV audio file.

    Expects a mono 16-bit PCM WAV whose sample rate matches the Porcupine model.
    Returns True if the wake word is detected, False otherwise.
    """
    ACCESS_KEY = "s0QFZ1oBiipJz+2mSNHz1jWPstzR4ExZGDMsiii+tK6XnDddvv5bKQ=="

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[os.path.join("wakeword", "models", "hello_privox.ppn")]
    )

    try:
        # Read audio using soundfile (supports WAV, FLAC, etc.)
        audio, sr = sf.read(file_path, dtype="float32")

        # Convert to mono if needed
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        target_sr = porcupine.sample_rate

        # Resample if necessary using torchaudio
        if sr != target_sr:
            try:
                tensor = torch.from_numpy(audio).unsqueeze(0)
                resampler = T.Resample(sr, target_sr)
                tensor = resampler(tensor)
                audio = tensor.squeeze(0).numpy()
            except Exception:
                # Fallback: if resampling fails, abort detection for this file
                return False

        # Convert float32 [-1,1] to int16 PCM
        pcm_int16 = (audio * 32767).astype("int16")

        frame_length = porcupine.frame_length
        total = len(pcm_int16)

        # Iterate in frames
        for start in range(0, total, frame_length):
            end = start + frame_length
            if end > total:
                break
            frame = pcm_int16[start:end]
            if len(frame) != frame_length:
                break

            # porcupine.process expects a sequence of ints
            result = porcupine.process(frame.tolist())
            if result >= 0:
                return True

        return False

    except FileNotFoundError:
        return False
    finally:
        porcupine.delete()
