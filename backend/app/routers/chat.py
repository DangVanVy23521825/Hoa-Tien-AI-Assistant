from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limiter
from app.db.session import get_db
from app.models import ChatHistory, Contact, Procedure, User
from app.schemas.chat import ChatHistoryOut, ChatRequest, ChatResponse, FeedbackRequest, PublicStatsOut
from app.services.deps import get_current_user_optional, get_current_user_required
from app.services.generation import generate
from app.services.retrieval import embed_query, retrieve
from app.services.smalltalk import SOURCE_TYPE as SMALLTALK_SOURCE_TYPE
from app.services.smalltalk import respond as smalltalk_respond
from app.services.smalltalk import respond_semantic as smalltalk_respond_semantic

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

    # Chào hỏi/cảm ơn xử lý trước retrieval: không có tài liệu nào là câu trả lời đúng
    # cho "xin chào", để nó rơi vào fallback thì người dân nhận nguyên văn câu từ chối.
    # Chặn ở đây còn tiết kiệm 1 lần gọi API embedding cho mỗi câu chào.
    result = smalltalk_respond(payload.question)
    if result is None:
        hits = retrieve(db, payload.question, top_k=3)
        if not hits:
            # Tầng 2 chỉ chạy khi không tra cứu được gì, nên câu hỏi hợp lệ không bao
            # giờ bị lớp xã giao cướp mất. embed_query có cache nên không tốn thêm
            # lần gọi API nào — vector này retrieval vừa tính xong.
            result = smalltalk_respond_semantic(embed_query(payload.question))
        if result is None:
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


def _top_procedures(db: Session, limit: int) -> list[tuple[str, int]]:
    """[(tên thủ tục, số lượt hỏi)] xếp giảm dần, join qua code trong matched_source_id."""
    rows = (
        db.query(ChatHistory.matched_source_id, func.count().label("n"))
        .filter(ChatHistory.matched_source_type == "procedure", ChatHistory.matched_source_id.isnot(None))
        .group_by(ChatHistory.matched_source_id)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    names = {p.code: p.name for p in db.query(Procedure).filter(Procedure.code.in_([r[0] for r in rows]))}
    return [(names[code], n) for code, n in rows if code in names]


@router.get("/stats/public", response_model=PublicStatsOut)
def public_stats(db: Session = Depends(get_db)):
    # Chỉ đếm lượt thực sự trả lời được từ dữ liệu xã — không tính chào hỏi/cảm ơn.
    total = (
        db.query(ChatHistory)
        .filter(ChatHistory.matched_source_type.notin_(["none", SMALLTALK_SOURCE_TYPE]))
        .count()
    )
    return PublicStatsOut(total_answered=total, top_questions=[name for name, _ in _top_procedures(db, 4)])


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
