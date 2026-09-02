import os
from sqlalchemy.orm import Session
from app.database.models import BankTransaction, LedgerEntry, Match, ExceptionRecord, ReconciliationRun
from app.matching.candidate_generator import CandidateGenerator
from app.matching.rule_matcher import RuleMatcher

class ReconciliationService:
    def __init__(self, db: Session):
        self.db = db
        self.candidate_generator = CandidateGenerator(
            amount_tolerance=float(os.getenv("AMOUNT_TOLERANCE", 1.0)),
            date_tolerance_days=int(os.getenv("DATE_TOLERANCE_DAYS", 2))
        )
        self.auto_match_threshold = float(os.getenv("AUTO_MATCH_THRESHOLD", 0.90))
        self.review_threshold = float(os.getenv("REVIEW_THRESHOLD", 0.70))

    def run_deterministic_reconciliation(self, run_id: str):
        """
        Runs the deterministic matching engine against all records for a given run_id.
        """
        run = self.db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")

        bank_txns = self.db.query(BankTransaction).filter(BankTransaction.run_id == run_id).all()
        ledger_pool = self.db.query(LedgerEntry).filter(LedgerEntry.run_id == run_id).all()

        matched_count = 0
        exception_count = 0

        for bank in bank_txns:
            # 1. Generate Candidates
            candidates = self.candidate_generator.generate_candidates(bank, ledger_pool)

            # 2. No candidates found
            if not candidates:
                self._create_exception(
                    run_id=run_id,
                    source_id=bank.transaction_id,
                    exc_type="MISSING_LEDGER_ENTRY",
                    reason="No ledger candidates found within amount and date tolerances.",
                    severity="HIGH"
                )
                exception_count += 1
                continue

            # 3. Score Candidates
            best_candidate = None
            best_score = -1.0
            best_evidence = None

            for ledger in candidates:
                result = RuleMatcher.calculate_confidence(bank, ledger)
                if result["confidence_score"] > best_score:
                    best_score = result["confidence_score"]
                    best_candidate = ledger
                    best_evidence = result["evidence"]

            # 4. Apply Thresholds
            if best_score >= self.auto_match_threshold:
                # AUTO MATCH
                new_match = Match(
                    run_id=run_id,
                    bank_transaction_id=bank.transaction_id,
                    ledger_entry_id=best_candidate.ledger_id,
                    confidence_score=best_score,
                    match_method="RULE_BASED",
                    status="VERIFIED",
                    evidence={"reasons": best_evidence}
                )
                self.db.add(new_match)
                # Remove from pool so it can't be matched again (One-to-One constraint)
                ledger_pool.remove(best_candidate)
                matched_count += 1
            else:
                # AMBIGUOUS -> Send to Exception Queue
                self._create_exception(
                    run_id=run_id,
                    source_id=bank.transaction_id,
                    candidate_id=best_candidate.ledger_id if best_candidate else None,
                    exc_type="LOW_CONFIDENCE",
                    reason=f"Best match score was {best_score:.2f}, which is below the {self.auto_match_threshold} threshold.",
                    severity="MEDIUM",
                    confidence=best_score
                )
                exception_count += 1

        # 5. Update Run Status
        run.matched_records = matched_count
        run.exceptions_count = exception_count
        run.unmatched_records = len(bank_txns) - matched_count
        run.status = "COMPLETED"
        
        self.db.commit()
        return run

    def _create_exception(self, run_id, source_id, exc_type, reason, severity, candidate_id=None, confidence=None):
        import uuid
        exc = ExceptionRecord(
            exception_id=f"EXC-{uuid.uuid4().hex[:6].upper()}",
            run_id=run_id,
            source_record_id=source_id,
            candidate_record_id=candidate_id,
            exception_type=exc_type,
            severity=severity,
            confidence_score=confidence,
            reason=reason,
            recommended_action="REQUIRES_REVIEW",
            status="OPEN"
        )
        self.db.add(exc)