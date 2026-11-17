"""STT Service: faster-whisper small int8 (CPU) with timestamped segments."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


@dataclass
class TranscriptSegment:
    """One timestamped segment of a transcript."""
    segment_index: int
    start_ms: int
    end_ms: int
    text: str
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_index": self.segment_index,
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "text": self.text,
            "confidence": self.confidence,
        }


@dataclass
class TranscriptResult:
    """Result of transcribing an audio file."""
    segments: list[TranscriptSegment] = field(default_factory=list)
    language: str = "en"
    duration_s: float = 0.0
    elapsed_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "duration_s": round(self.duration_s, 2),
            "elapsed_s": round(self.elapsed_s, 2),
            "segments": [s.to_dict() for s in self.segments],
        }


class STTService:
    """Encapsulates faster-whisper with small int8 model (from P0 benchmark)."""

    _instance: "STTService | None" = None

    def __new__(cls) -> "STTService":
        # Singleton: loading Whisper takes ~4 s and ~1.5 GB RAM.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = WhisperModel(
                "small",
                device=os.getenv("WHISPER_DEVICE", "cpu"),
                compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
            )
        return cls._instance

    def get_duration_ms(self, audio_path: Path) -> int:
        """Get audio duration in milliseconds."""
        import av
        with av.open(str(audio_path), mode="r") as container:
            if container.duration is not None:
                return int(float(container.duration) / av.time_base * 1000)
            for stream in container.streams:
                if stream.duration is not None and stream.time_base is not None:
                    return int(float(stream.duration * stream.time_base) * 1000)
        return 0

    def transcribe(self, audio_path: Path, language: str = "en") -> TranscriptResult:
        """Transcribe an audio file into timestamped segments."""
        import time
        t0 = time.time()

        segments_iter, info = self._model.transcribe(
            str(audio_path),
            beam_size=5,
            language=language,
            vad_filter=True,  # skip silence for faster processing
        )

        segments: list[TranscriptSegment] = []
        for idx, seg in enumerate(segments_iter):
            # faster-whisper returns segment.text with leading space; strip it.
            text = seg.text.strip()
            if not text:
                continue
            segments.append(
                TranscriptSegment(
                    segment_index=idx,
                    start_ms=int(seg.start * 1000),
                    end_ms=int(seg.end * 1000),
                    text=text,
                    confidence=None,  # faster-whisper doesn't expose avg_logprob per segment here
                )
            )

        elapsed = time.time() - t0
        return TranscriptResult(
            segments=segments,
            language=info.language or language,
            duration_s=info.duration or 0.0,
            elapsed_s=elapsed,
        )