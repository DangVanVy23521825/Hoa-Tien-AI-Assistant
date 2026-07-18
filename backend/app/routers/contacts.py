from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Contact
from app.schemas.contact import ContactOut

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=ContactOut)
def get_contacts(db: Session = Depends(get_db)):
    contact = db.query(Contact).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu liên hệ")
    return contact
