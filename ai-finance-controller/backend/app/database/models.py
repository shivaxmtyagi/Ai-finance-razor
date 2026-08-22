from sqlalchemy import Column, String, Float, Date, Boolean, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.sql import func
from app.database.database import Base

class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="IN_PROGRESS") # IN_PROGRESS, COMPLETED, FAILED
    total_records = Column(Integer, default=0)
    matched_records = Column(Integer, default=0)
    unmatched_records = Column(Integer, default=0)
    exceptions_count = Column(Integer, default=0)
    metrics = Column(JSON, nullable=True) # stores precision, recall, f1
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    transaction_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("reconciliation_runs.id"))
    transaction_date = Column(Date)
    description = Column(String)
    amount = Column(Float)
    currency = Column(String)
    reference = Column(String, index=True)
    transaction_type = Column(String)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    ledger_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("reconciliation_runs.id"))
    entry_date = Column(Date)
    vendor = Column(String)
    description = Column(String)
    amount = Column(Float)
    currency = Column(String)
    reference = Column(String, index=True)
    account = Column(String)

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("reconciliation_runs.id"))
    bank_transaction_id = Column(String, ForeignKey("bank_transactions.transaction_id"))
    ledger_entry_id = Column(String, ForeignKey("ledger_entries.ledger_id"))
    confidence_score = Column(Float)
    match_method = Column(String) # EXACT, FUZZY, SEMANTIC, LLM, HUMAN
    status = Column(String) # VERIFIED, REJECTED
    evidence = Column(JSON) # Why it matched
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ExceptionRecord(Base):
    __tablename__ = "exceptions"
    exception_id = Column(String, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("reconciliation_runs.id"))
    source_record_id = Column(String)
    candidate_record_id = Column(String, nullable=True)
    exception_type = Column(String) # AMOUNT_MISMATCH, VENDOR_AMBIGUITY, etc.
    severity = Column(String) # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score = Column(Float, nullable=True)
    reason = Column(String)
    recommended_action = Column(String)
    status = Column(String, default="OPEN") # OPEN, RESOLVED
    resolution = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("reconciliation_runs.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String)
    record_id = Column(String, nullable=True)
    actor = Column(String) # SYSTEM, AGENT_NODE, HUMAN_USER
    metadata_info = Column(JSON)