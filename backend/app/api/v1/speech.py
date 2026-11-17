"""Speech synthesis endpoints."""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.schemas.speech import SynthesizeRequest, SynthesizeResponse
from app.services.tts_service import TTSService

router = APIRouter(tags=["speech"])


@router.post(
    "/speech/synthesize",
    response_model=SynthesizeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def synthesize(body: SynthesizeRequest) -> SynthesizeResponse:
    """Synthesize text to a WAV file. Returns metadata + URL to download."""
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail="Text too long (max 2000 chars)")

    svc = TTSService()
    result = svc.synthesize(text)

    # Return filename; full path is under /audio/tts/{filename}
    filename = Path(result.audio_path).name
    return SynthesizeResponse(
        audio_id=filename,
        download_url=f"/api/v1/speech/audio/{filename}",
        size_bytes=result.size_bytes,
        elapsed_s=round(result.elapsed_s, 2),
    )


@router.get("/speech/audio/{filename}")
async def get_audio(filename: str) -> FileResponse:
    """Serve a TTS-generated WAV file (loopback only)."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = settings.STORAGE_ROOT / "tts" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(str(path), media_type="audio/wav", filename=filename)