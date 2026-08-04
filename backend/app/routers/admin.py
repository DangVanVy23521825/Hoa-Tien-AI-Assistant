import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Contact, Faq, KnowledgeArticle, Procedure, User
from app.schemas.contact import ContactOut, ContactUpdate
from app.schemas.faq import FaqCreate, FaqOut, FaqUpdate
from app.schemas.knowledge_article import KnowledgeArticleCreate, KnowledgeArticleOut, KnowledgeArticleUpdate
from app.schemas.procedure import ProcedureCreate, ProcedureOut, ProcedureUpdate
from app.services.deps import require_admin
from app.services.embeddings import embed_text

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _try_embed(text: str) -> list[float] | None:
    try:
        return embed_text(text, "RETRIEVAL_DOCUMENT")
    except Exception:  # noqa: BLE001 — không chặn CRUD nếu Gemini lỗi tạm thời
        return None


def _procedure_embed_source(p: Procedure) -> str:
    return " ".join([p.name, p.category, p.description, " ".join(p.keywords or [])])


def _faq_embed_source(f: Faq) -> str:
    return " ".join([f.question, " ".join(f.keywords or []), f.answer])


def _article_embed_source(a: KnowledgeArticle) -> str:
    return " ".join([a.title, " ".join(a.keywords or []), a.content])


# ---------- Procedures ----------
@router.post("/procedures", response_model=ProcedureOut, status_code=201)
def create_procedure(payload: ProcedureCreate, db: Session = Depends(get_db)):
    if db.query(Procedure).filter(Procedure.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Mã thủ tục đã tồn tại")
    proc = Procedure(**payload.model_dump())
    proc.embedding = _try_embed(_procedure_embed_source(proc))
    db.add(proc)
    db.commit()
    db.refresh(proc)
    return proc


@router.put("/procedures/{procedure_id}", response_model=ProcedureOut)
def update_procedure(procedure_id: uuid.UUID, payload: ProcedureUpdate, db: Session = Depends(get_db)):
    proc = db.get(Procedure, procedure_id)
    if not proc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thủ tục")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(proc, k, v)
    proc.embedding = _try_embed(_procedure_embed_source(proc))
    db.commit()
    db.refresh(proc)
    return proc


@router.delete("/procedures/{procedure_id}", status_code=204)
def delete_procedure(procedure_id: uuid.UUID, db: Session = Depends(get_db)):
    proc = db.get(Procedure, procedure_id)
    if not proc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thủ tục")
    db.delete(proc)
    db.commit()


# ---------- FAQ ----------
@router.post("/faq", response_model=FaqOut, status_code=201)
def create_faq(payload: FaqCreate, db: Session = Depends(get_db)):
    f = Faq(**payload.model_dump())
    f.embedding = _try_embed(_faq_embed_source(f))
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.put("/faq/{faq_id}", response_model=FaqOut)
def update_faq(faq_id: uuid.UUID, payload: FaqUpdate, db: Session = Depends(get_db)):
    f = db.get(Faq, faq_id)
    if not f:
        raise HTTPException(status_code=404, detail="Không tìm thấy FAQ")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    f.embedding = _try_embed(_faq_embed_source(f))
    db.commit()
    db.refresh(f)
    return f


@router.delete("/faq/{faq_id}", status_code=204)
def delete_faq(faq_id: uuid.UUID, db: Session = Depends(get_db)):
    f = db.get(Faq, faq_id)
    if not f:
        raise HTTPException(status_code=404, detail="Không tìm thấy FAQ")
    db.delete(f)
    db.commit()


# ---------- Knowledge articles (lịch sử / địa danh / làng nghề) ----------
@router.post("/articles", response_model=KnowledgeArticleOut, status_code=201)
def create_article(payload: KnowledgeArticleCreate, db: Session = Depends(get_db)):
    article = KnowledgeArticle(**payload.model_dump())
    article.embedding = _try_embed(_article_embed_source(article))
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@router.put("/articles/{article_id}", response_model=KnowledgeArticleOut)
def update_article(article_id: uuid.UUID, payload: KnowledgeArticleUpdate, db: Session = Depends(get_db)):
    article = db.get(KnowledgeArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(article, k, v)
    article.embedding = _try_embed(_article_embed_source(article))
    db.commit()
    db.refresh(article)
    return article


@router.delete("/articles/{article_id}", status_code=204)
def delete_article(article_id: uuid.UUID, db: Session = Depends(get_db)):
    article = db.get(KnowledgeArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
    db.delete(article)
    db.commit()


# ---------- Contact ----------
@router.put("/contacts", response_model=ContactOut)
def update_contact(payload: ContactUpdate, db: Session = Depends(get_db)):
    contact = db.query(Contact).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu liên hệ để cập nhật")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(contact, k, v)
    db.commit()
    db.refresh(contact)
    return contact
