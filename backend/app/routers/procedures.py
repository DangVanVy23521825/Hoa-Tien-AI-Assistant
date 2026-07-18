from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Procedure
from app.schemas.procedure import ProcedureOut

router = APIRouter(prefix="/procedures", tags=["procedures"])


@router.get("", response_model=list[ProcedureOut])
def list_procedures(db: Session = Depends(get_db)):
    return db.query(Procedure).order_by(Procedure.category, Procedure.name).all()


@router.get("/{procedure_id}", response_model=ProcedureOut)
def get_procedure(procedure_id: str, db: Session = Depends(get_db)):
    proc = db.query(Procedure).filter(
        (Procedure.code == procedure_id)
    ).first()
    if not proc:
        try:
            import uuid

            proc = db.get(Procedure, uuid.UUID(procedure_id))
        except ValueError:
            proc = None
    if not proc:
        raise HTTPException(status_code=404, detail="Không tìm thấy thủ tục")
    return proc
