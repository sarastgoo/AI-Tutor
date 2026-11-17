"""Speaking attempts: upload recording, transcribe, get feedback, TTS reply."""
import uuid as uuid_lib
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.config import settings
from app.models.learning import LearningSession, SpeakingAttempt
from app.schemas.speaking import SpeakingAttemptDetail
from app.services.llm_service import ChatMessage, LLMService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

router = APIRouter(tags=["speaking"])


FEEDBACK_SYSTEM_PROMPT = """You are an English tutor evaluating a learner's spoken response.

Given the transcript of what the learner said, provide:
1. A brief, encouraging overall assessment (1 sentence).
2. Specific grammar/vocabulary corrections (only meaningful errors, not style preferences).
3. One natural English example the learner can learn from.

Keep feedback concise (max 100 words). Use English.
Do NOT score pronunciation — we don't have acoustic analysis yet.
"""


@router.post(
    "/speaking/attempts",
    response_model=SpeakingAttemptDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_speaking_attempt(
    session: SessionDep,
    session_id: str = Form(...),
    audio: UploadFile = File(...),
) -> SpeakingAttemptDetail:
    """Upload a recording, transcribe, get feedback, synthesize reply."""
    # 1. Validate session exists
    sess = (
        await session.execute(select(LearningSession).where(LearningSession.id == session_id))
    ).scalar_one_or_none()
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Validate MIME and size
    if audio.content_type not in ("audio/wav", "audio/mpeg", "audio/webm", "audio/ogg"):
        raise HTTPException(status_code=400, detail=f"Unsupported audio type: {audio.content_type}")
    content = await audio.read()
    if len(content) > 20 * 1024 * 1024:  # 20 MB cap
        raise HTTPException(status_code=413, detail="Audio file too large (max 20 MB)")
    if len(content) < 1000:
        raise HTTPException(status_code=400, detail="Audio file too small (likely empty)")

    # 3. Save to storage
    recordings_dir = settings.STORAGE_ROOT / "recordings" / str(sess.id)
    recordings_dir.mkdir(parents=True, exist_ok=True)
    ext = ".webm" if audio.content_type == "audio/webm" else ".wav"
    rec_path = recordings_dir / f"{uuid_lib.uuid4().hex}{ext}"
    rec_path.write_bytes(content)

    # 4. Transcribe (STT)
    stt = STTService()
    transcript_result = stt.transcribe(rec_path)
    full_transcript = " ".join(s.text for s in transcript_result.segments).strip()
    if not full_transcript:
        raise HTTPException(status_code=400, detail="Could not transcribe audio (empty result)")

    # 5. Get feedback from LLM
    llm = LLMService()
    feedback_messages = [
        ChatMessage(role="system", content=FEEDBACK_SYSTEM_PROMPT),
        ChatMessage(role="user", content=f"Transcript: {full_transcript}"),
    ]
    feedback_resp = await llm.chat(feedback_messages, temperature=0.5, num_predict=1000)
    feedback_text = feedback_resp.content

    # 6. Synthesize the tutor's feedback as audio (so user can hear it)
    tts = TTSService()
    tts_result = tts.synthesize(feedback_text)

    # 7. Persist attempt
    attempt = SpeakingAttempt(
        session_id=sess.id,
        recording_path=str(rec_path),
        transcript=full_transcript,
        stt_profile="faster-whisper:small:int8",
        feedback={"text": feedback_text},
        pronunciation_status="not_assessed",
    )
    session.add(attempt)
    await session.flush()
    await session.refresh(attempt)

    return SpeakingAttemptDetail(
        id=attempt.id,
        transcript=full_transcript,
        feedback_text=feedback_text,
        reply_text=None,
        reply_audio_url=f"/api/v1/speech/audio/{Path(tts_result.audio_path).name}",
        pronunciation_status=attempt.pronunciation_status,
    )


@router.get("/speaking/attempts/{attempt_id}")
async def get_attempt(attempt_id: str, session: SessionDep) -> dict:
    stmt = select(SpeakingAttempt).where(SpeakingAttempt.id == attempt_id)
    attempt = (await session.execute(stmt)).scalar_one_or_none()
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return {
        "id": str(attempt.id),
        "transcript": attempt.transcript,
        "feedback": attempt.feedback,
        "pronunciation_status": attempt.pronunciation_status,
        "recording_path": attempt.recording_path,
        "created_at": attempt.created_at.isoformat(),
    }