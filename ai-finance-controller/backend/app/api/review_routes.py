from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.database import SessionLocal
from app.database.models import ExceptionRecord, Match

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ManualResolutionRequest(BaseModel):
    bank_transaction_id: str
    ledger_entry_id: str
    notes: str

@router.get("/exceptions/{run_id}")
def get_exceptions(run_id: str, db: Session = Depends(get_db)):
    exceptions = db.query(ExceptionRecord).filter(
        ExceptionRecord.run_id == run_id,
        ExceptionRecord.status == "PENDING_REVIEW"
    ).all()
    return {"count": len(exceptions), "exceptions": exceptions}

@router.post("/exceptions/{run_id}/resolve")
def resolve_exception(run_id: str, request: ManualResolutionRequest, db: Session = Depends(get_db)):
    exc = db.query(ExceptionRecord).filter(
        ExceptionRecord.run_id == run_id,
        ExceptionRecord.source_record_id == request.bank_transaction_id
    ).first()
    
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found.")
        
    new_match = Match(
        run_id=run_id,
        bank_transaction_id=request.bank_transaction_id,
        ledger_entry_id=request.ledger_entry_id,
        confidence_score=1.0,
        match_method="MANUAL_REVIEW",
        status="VERIFIED",
        evidence={"notes": request.notes}
    )
    db.add(new_match)
    
    exc.status = "RESOLVED_MANUALLY"
    db.commit()
    
    return {"message": "Match manually verified and saved."}