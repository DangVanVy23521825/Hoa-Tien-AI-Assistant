from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Faq
from app.schemas.faq import FaqOut

router = APIRouter(prefix="/faq", tags=["faq"])


@router.get("", response_model=list[FaqOut])
def list_faq(db: Session = Depends(get_db)):
    return db.query(Faq).order_by(Faq.created_at).all()
