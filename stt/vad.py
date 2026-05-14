import torch
import numpy as np

class SileroVAD:
    """
    Streaming-safe Silero VAD wrapper.

    Uses buffered audio (0.5s) for reliable speech detection.
    No C++ build tools required.
    """

    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

        # Load Silero VAD model
        self.model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True
        )

        self.get_speech_timestamps = utils[0]

        # Internal buffer for VAD decision
        self.vad_buffer = []
        self.vad_samples = 0

        # Minimum audio needed for VAD decision (0.5 sec)
        self.min_vad_samples = int(0.5 * self.sample_rate)

    def is_speech(self, audio_chunk):
        """
        Accepts small float32 audio chunks (e.g., 1024 samples).
        Internally buffers until enough audio is collected.
        Returns True only when speech is confidently detected.
        """

        if audio_chunk is None or len(audio_chunk) == 0:
            return False

        # Convert to numpy float32
        audio_chunk = np.asarray(audio_chunk, dtype=np.float32)

        # Buffer audio
        self.vad_buffer.append(audio_chunk)
        self.vad_samples += len(audio_chunk)

        # Not enough audio yet → no decision
        if self.vad_samples < self.min_vad_samples:
            return False

        # Run Silero VAD on buffered audio
        audio = np.concatenate(self.vad_buffer)
        self.vad_buffer.clear()
        self.vad_samples = 0

        try:
            speech_timestamps = self.get_speech_timestamps(
                audio,
                self.model,
                sampling_rate=self.sample_rate
            )
            return len(speech_timestamps) > 0

        except Exception:
            return False
