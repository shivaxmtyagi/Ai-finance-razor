import os
from app.database.database import engine, Base, SessionLocal
from app.data.loader import DataLoader
from app.services.reconciliation_service import ReconciliationService

def run_test():
    print("1. Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Resolve paths to the data folder
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bank_csv = os.path.join(base_dir, "data", "bank_transactions.csv")
        ledger_csv = os.path.join(base_dir, "data", "ledger_entries.csv")
        
        if not os.path.exists(bank_csv):
            print(f"❌ Error: Could not find {bank_csv}")
            return

        print("2. Loading and normalizing CSV data...")
        loader = DataLoader(db)
        run_id = loader.load_reconciliation_files(bank_csv, ledger_csv)
        print(f"   ✅ Data loaded! Run ID: {run_id}")
        
        print("3. Running Deterministic Engine...")
        service = ReconciliationService(db)
        run_result = service.run_deterministic_reconciliation(run_id)
        
        print("\n" + "="*50)
        print("🎯 RECONCILIATION COMPLETE")
        print("="*50)
        print(f"Total Bank Records:  {run_result.total_records}")
        print(f"Auto-Matched:        {run_result.matched_records} 🟢")
        print(f"Exceptions (Review): {run_result.exceptions_count} 🟡")
        print(f"Unmatched:           {run_result.unmatched_records} 🔴")
        print("="*50)

    except Exception as e:
        print(f"❌ Error during execution: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_test()