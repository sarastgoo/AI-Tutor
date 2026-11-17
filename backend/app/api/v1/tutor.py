"""Tutor endpoints: create sessions, send messages, list history."""
import uuid as uuid_lib

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models.books import Book
from app.models.learning import ChatMessage, LearningSession
from app.schemas.tutor import (
    CreateSessionRequest,
    SendMessageRequest,
    SendMessageResponse,
    SessionResponse,
)
from app.services.tutor_graph import TutorGraph

router = APIRouter(tags=["tutor"])


@router.post(
    "/tutor/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/tutor/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    body: CreateSessionRequest, session: SessionDep
) -> LearningSession:
    book = (
        await session.execute(select(Book).where(Book.id == body.book_id))
    ).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # پیدا کردن یا ساختن کاربر پیش‌فرض
    from app.models.users import User
    user = (await session.execute(select(User).limit(1))).scalar_one_or_none()
    if user is None:
        user = User(display_name="Local Learner")
        session.add(user)
        await session.flush()

    obj = LearningSession(
        user_id=user.id,  # <--- به جای None، شناسه کاربر را می‌دهیم
        book_id=body.book_id,
        active_node_id=body.active_node_id,
        mode=body.mode,
        status="active",
    )
    session.add(obj)
    await session.flush()
    await session.refresh(obj)
    return obj


@router.post(
    "/tutor/sessions/{session_id}/messages",
    response_model=SendMessageResponse,
)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    session: SessionDep,
) -> SendMessageResponse:
    sess = (
        await session.execute(select(LearningSession).where(LearningSession.id == session_id))
    ).scalar_one_or_none()
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 1. Persist user message
    user_msg = ChatMessage(
        session_id=sess.id,
        role="user",
        content=body.text,
        sources={},
    )
    session.add(user_msg)
    await session.flush()

    # 2. Load prior conversation (last 10 messages)
    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == sess.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    history_rows = list((await session.execute(history_stmt)).scalars())
    history_rows.reverse()  # chronological
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history_rows
        if m.role in ("user", "assistant")
    ]

    # 3. Run tutor
    tutor = TutorGraph()
    turn = await tutor.respond(
        session=session,
        book_id=str(sess.book_id),
        user_message=body.text,
        conversation_history=conversation_history,
    )

    # 4. Persist assistant message
    assistant_msg = ChatMessage(
        session_id=sess.id,
        role="assistant",
        content=turn.reply,
        sources={"items": turn.sources},
    )
    session.add(assistant_msg)
    await session.flush()

    return SendMessageResponse(
        user_message_id=user_msg.id,
        assistant_message_id=assistant_msg.id,
        reply=turn.reply,
        sources=turn.sources,
        elapsed_s=round(turn.elapsed_s, 2),
    )


@router.get("/tutor/sessions/{session_id}/messages")
async def list_messages(session_id: str, session: SessionDep) -> dict:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    rows = list((await session.execute(stmt)).scalars())
    return {
        "session_id": session_id,
        "count": len(rows),
        "items": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "created_at": m.created_at.isoformat(),
            }
            for m in rows
        ],
    }