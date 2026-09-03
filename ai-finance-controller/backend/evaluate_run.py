import os
import json
from app.database.database import SessionLocal
from app.database.models import Match, ReconciliationRun

def run_evaluation():
    db = SessionLocal()
    print("📊 Starting Evaluation Pipeline...")
    try:
        run = db.query(ReconciliationRun).order_by(ReconciliationRun.id.desc()).first()
        if not run:
            print("❌ No reconciliation runs found in the database.")
            return

        print(f"Target Run ID: {run.id}")

        # FIX: Navigate UP out of 'backend' to the main project folder
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        gt_path = os.path.join(base_dir, "data", "ground_truth.json")
        
        if not os.path.exists(gt_path):
            print(f"❌ ground_truth.json not found in: {gt_path}")
            return
            
        with open(gt_path, 'r') as f:
            truth_data = json.load(f)
            
        true_matches = {}
        for item in truth_data:
            b_id = item.get("transaction_id") or item.get("bank_id")
            l_id = item.get("ledger_id")
            if b_id and l_id:
                true_matches[b_id] = l_id

        total_true = len(true_matches)
        
        system_matches = db.query(Match).filter(Match.run_id == run.id).all()
        
        true_positives = 0
        false_positives = 0
        
        for m in system_matches:
            actual_ledger = true_matches.get(m.bank_transaction_id)
            if actual_ledger == m.ledger_entry_id:
                true_positives += 1
            else:
                false_positives += 1
                
        false_negatives = total_true - true_positives
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        print("\n" + "="*50)
        print("📈 FINAL ENGINE PERFORMANCE REPORT")
        print("="*50)
        print(f"Total True Matches Hidden in Data: {total_true}")
        print(f"Engine Guessed Correctly (TP):     {true_positives} 🟢")
        print(f"Engine Hallucinated/Wrong (FP):    {false_positives} 🔴")
        print(f"Engine Missed Entirely (FN):       {false_negatives} 🟡")
        print("-" * 50)
        print(f"Precision (Accuracy of its matches): {precision*100:.1f}%")
        print(f"Recall (Percentage of total found):  {recall*100:.1f}%")
        print(f"F1 Score (Overall Grade):            {f1_score*100:.1f}%")
        print("="*50)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_evaluation()