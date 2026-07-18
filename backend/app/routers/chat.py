from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.db.session import get_db
from app.models import ChatHistory, Contact, User
from app.schemas.chat import ChatHistoryOut, ChatRequest, ChatResponse
from app.services.deps import get_current_user_optional, get_current_user_required
from app.services.generation import generate
from app.services.retrieval import retrieve

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit("30/minute")
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

    # Chỉ lưu lịch sử nếu người dùng đã đăng nhập (khách vãng lai không bị ép lưu)
    if current_user is not None:
        entry = ChatHistory(
            user_id=current_user.id,
            question=payload.question,
            answer=result["answer_html"],
            matched_source_type=result["matched_source_type"],
            matched_source_id=result.get("matched_source_id"),
        )
        db.add(entry)
        db.commit()

    return ChatResponse(
        answer_html=result["answer_html"],
        source=result["source"],
        matched=result["matched"],
        matched_source_type=result["matched_source_type"],
    )


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
