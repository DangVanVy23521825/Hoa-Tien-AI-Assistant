import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Contact, Faq, Procedure, User
from app.schemas.contact import ContactOut, ContactUpdate
from app.schemas.faq import FaqCreate, FaqOut, FaqUpdate
from app.schemas.procedure import ProcedureCreate, ProcedureOut, ProcedureUpdate
from app.services.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------- Procedures ----------
@router.post("/procedures", response_model=ProcedureOut, status_code=201)
def create_procedure(payload: ProcedureCreate, db: Session = Depends(get_db)):
    if db.query(Procedure).filter(Procedure.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Mã thủ tục đã tồn tại")
    proc = Procedure(**payload.model_dump())
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
