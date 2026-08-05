from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import get_db
from app.models import ChatHistory, Contact, User
from app.schemas.chat import ChatHistoryOut, ChatRequest, ChatResponse, FeedbackRequest
from app.services.deps import get_current_user_optional, get_current_user_required
from app.services.generation import generate
from app.services.retrieval import retrieve

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit(settings.rate_limit_chat)
def chat(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    contact = db.query(Contact).first()
    fallback_phone = contact.phone if contact else ""

    hits = retrieve(db, payload.question, top_k=3)
    result = generate(payload.question, hits, fallback_phone=fallback_phone)

    # Lưu mọi lượt chat (kể cả khách vãng lai, user_id=None) để thống kê câu hỏi
    # phổ biến & câu chưa trả lời được. /chat/history vẫn lọc theo user_id nên
    # khách ẩn danh không thấy gì thay đổi.
    entry = ChatHistory(
        user_id=current_user.id if current_user else None,
        question=payload.question,
        answer=result["answer_html"],
        matched_source_type=result["matched_source_type"],
        matched_source_id=result.get("matched_source_id"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return ChatResponse(
        answer_html=result["answer_html"],
        source=result["source"],
        matched=result["matched"],
        matched_source_type=result["matched_source_type"],
        online_url=result.get("online_url"),
        message_id=entry.id,
        matched_source_id=result.get("matched_source_id"),
    )


@router.post("/feedback", status_code=204)
@limiter.limit(settings.rate_limit_chat)
def chat_feedback(request: Request, payload: FeedbackRequest, db: Session = Depends(get_db)):
    """Ghi nhận 👍👎 — không cần đăng nhập, message_id là UUID không đoán được."""
    entry = db.get(ChatHistory, payload.message_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu trả lời")
    entry.feedback_helpful = payload.helpful
    db.commit()


@router.get("/history", response_model=list[ChatHistoryOut])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .limit(50)
        .all()
    )
