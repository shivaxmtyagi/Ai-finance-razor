from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database.models import Match, ExceptionRecord

class VerificationService:
    def __init__(self, db: Session):
        self.db = db

    def verify_and_commit_ai_matches(self, run_id: str, ai_matches: List[Dict[str, Any]]) -> dict:
        used_bank_ids = set()
        used_ledger_ids = set()
        verified_count = 0
        rejected_count = 0
        
        for match_data in ai_matches:
            bank_id = match_data["bank_id"]
            ledger_id = match_data["ledger_id"]
            
            # Constraint 1: Strict One-to-One Matching 
            if bank_id in used_bank_ids or ledger_id in used_ledger_ids:
                self._reject_match(run_id, bank_id, "AI attempted duplicate match (One-to-One Violation)")
                rejected_count += 1
                continue
                
            # Commit valid AI match
            new_match = Match(
                run_id=run_id,
                bank_transaction_id=bank_id,
                ledger_entry_id=ledger_id,
                confidence_score=match_data["confidence"],
                match_method="AI_AGENT",
                status="VERIFIED",
                evidence={"reasoning": match_data["reasoning"], "flags": match_data["risk_flags"]}
            )
            self.db.add(new_match)
            
            # Close out the old Exception
            old_exc = self.db.query(ExceptionRecord).filter(
                ExceptionRecord.source_record_id == bank_id,
                ExceptionRecord.run_id == run_id
            ).first()
            if old_exc:
                old_exc.status = "RESOLVED_BY_AI"
                
            used_bank_ids.add(bank_id)
            used_ledger_ids.add(ledger_id)
            verified_count += 1
            
        self.db.commit()
        return {"verified": verified_count, "rejected": rejected_count}
        
    def _reject_match(self, run_id: str, bank_id: str, reason: str):
        exc = self.db.query(ExceptionRecord).filter(
            ExceptionRecord.source_record_id == bank_id,
            ExceptionRecord.run_id == run_id
        ).first()
        if exc:
            exc.reason = f"{exc.reason} | AI REJECTED: {reason}"
            exc.severity = "CRITICAL"