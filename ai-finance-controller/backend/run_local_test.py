from app.services.verification_service import VerificationService
import os
from dotenv import load_dotenv
load_dotenv()

from app.database.database import engine, Base, SessionLocal
from app.data.loader import DataLoader
from app.services.reconciliation_service import ReconciliationService
from app.database.models import ExceptionRecord, BankTransaction, LedgerEntry
from app.agent.graph import reconciliation_agent

def run_test():
    print("1. Creating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bank_csv = os.path.join(base_dir, "data", "bank_transactions.csv")
        ledger_csv = os.path.join(base_dir, "data", "ledger_entries.csv")

        print("2. Loading CSV data...")
        loader = DataLoader(db)
        run_id = loader.load_reconciliation_files(bank_csv, ledger_csv)
        
        print("3. Running Deterministic Engine...")
        service = ReconciliationService(db)
        run_result = service.run_deterministic_reconciliation(run_id)
        
        print("\n" + "="*50)
        print("🎯 DETERMINISTIC ENGINE COMPLETE")
        print("="*50)
        print(f"Exceptions generated: {run_result.exceptions_count} 🟡")
        
        print("\n4. 🧠 Waking up the AI Agent (Phases 5 & 6)...")
        # Pull the ambiguous records that deterministic math couldn't solve
        exceptions = db.query(ExceptionRecord).filter(
            ExceptionRecord.run_id == run_id,
            ExceptionRecord.candidate_record_id != None
        ).all()
        
        if not exceptions:
            print("No candidates found for the AI to analyze.")
            return
            
        print(f"Agent found {len(exceptions)} pairs. Calculating vectors and analyzing...")
        
        ambiguous_pairs = []
        for exc in exceptions:
            bank = db.query(BankTransaction).filter(BankTransaction.transaction_id == exc.source_record_id).first()
            ledger = db.query(LedgerEntry).filter(LedgerEntry.ledger_id == exc.candidate_record_id).first()
            
            ambiguous_pairs.append({
                "bank": {"transaction_id": bank.transaction_id, "description": bank.description, "amount": bank.amount, "reference": bank.reference},
                "ledger": {"ledger_id": ledger.ledger_id, "vendor": ledger.vendor, "description": ledger.description, "amount": ledger.amount},
                "similarities": {"rule_confidence": exc.confidence_score}
            })
            
        initial_state = {
            "run_id": run_id,
            "ambiguous_pairs": ambiguous_pairs,
            "current_index": 0,
            "resolved_matches": [],
            "final_exceptions": []
        }
        
        # Trigger the LangGraph Execution
        final_state = reconciliation_agent.invoke(initial_state)
        
        print("\n" + "="*50)
        print("🤖 AI AGENT RECONCILIATION COMPLETE")
        print("="*50)
        print(f"Total Reviewed:  {len(ambiguous_pairs)}")
        print(f"AI Matches:      {len(final_state['resolved_matches'])} 🟢")
        print(f"Hard Exceptions: {len(final_state['final_exceptions'])} 🔴")
        print("="*50)
        
        if final_state['resolved_matches']:
            sample = final_state['resolved_matches'][0]
            print("\n🔍 Sample AI Reasoning:")
            print(f"Confidence: {sample['confidence']:.2f}")
            print(f"Reasoning:  {sample['reasoning']}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
print("\n5. 🛡️ Running Verification Guardrails (Phase 8)...")
        verifier = VerificationService(db)
        audit_results = verifier.verify_and_commit_ai_matches(run_id, final_state["resolved_matches"])
        
        print("\n" + "="*50)
        print("🏛️ FINAL AUDIT COMPLETE")
        print("="*50)
        print(f"AI Matches Safely Committed: {audit_results['verified']} 🟢")
        print(f"AI Hallucinations Blocked:   {audit_results['rejected']} 🔴")
        print("="*50)