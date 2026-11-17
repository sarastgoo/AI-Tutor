"""TTS Service: Piper voice synthesis."""
import uuid
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import settings


@dataclass
class TTSResult:
    """Result of a TTS synthesis."""
    audio_path: str
    size_bytes: int
    elapsed_s: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "audio_path": self.audio_path,
            "size_bytes": self.size_bytes,
            "elapsed_s": round(self.elapsed_s, 2),
        }


class TTSService:
    """Wraps Piper TTS for English voice synthesis."""

    _voice = None  # Lazy-loaded (singleton)

    def __init__(self) -> None:
        if TTSService._voice is None:
            from piper.voice import PiperVoice
            TTSService._voice = PiperVoice.load(
                str(settings.PIPER_VOICE_PATH),
                config_path=str(settings.PIPER_VOICE_CONFIG),
            )

    @property
    def voice(self):
        return TTSService._voice

    def synthesize(self, text: str, out_dir: Path | None = None) -> TTSResult:
        """Synthesize text to a WAV file. Returns the file path."""
        import time
        t0 = time.time()

        out_dir = out_dir or (settings.STORAGE_ROOT / "tts")
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"tts_{uuid.uuid4().hex}.wav"
        out_path = out_dir / filename

        with wave.open(str(out_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            for chunk in self.voice.synthesize(text):
                wav_file.writeframes(chunk.audio_int16_bytes)

        elapsed = time.time() - t0
        return TTSResult(
            audio_path=str(out_path),
            size_bytes=out_path.stat().st_size,
            elapsed_s=elapsed,
        )