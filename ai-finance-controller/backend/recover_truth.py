import os
import json
import csv

def recover_ground_truth():
    print("🔍 Rebuilding missing ground_truth.json...")
    
    # FIX: Navigate UP out of the 'backend' folder to the main project folder
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    bank_path = os.path.join(data_dir, "bank_transactions.csv")
    ledger_path = os.path.join(data_dir, "ledger_entries.csv")
    out_path = os.path.join(data_dir, "ground_truth.json")
    
    if not os.path.exists(bank_path) or not os.path.exists(ledger_path):
        print(f"❌ Cannot find CSV files in: {data_dir}")
        return
        
    print(f"📂 Found CSV data in: {data_dir}")
    truth_list = []
    used_ledgers = set()
    
    with open(bank_path, 'r', encoding='utf-8') as bf, open(ledger_path, 'r', encoding='utf-8') as lf:
        bank_reader = list(csv.DictReader(bf))
        ledger_reader = list(csv.DictReader(lf))
        
        for b_row in bank_reader:
            b_id = b_row.get('transaction_id')
            b_amt = b_row.get('amount')
            
            for l_row in ledger_reader:
                l_id = l_row.get('ledger_id')
                l_amt = l_row.get('amount')
                
                if l_id not in used_ledgers and b_amt == l_amt:
                    truth_list.append({
                        "transaction_id": b_id,
                        "ledger_id": l_id
                    })
                    used_ledgers.add(l_id)
                    break
                    
    with open(out_path, 'w') as outf:
        json.dump(truth_list, outf, indent=4)
        
    print(f"✅ Successfully rebuilt ground_truth.json with {len(truth_list)} pairs!")

if __name__ == "__main__":
    recover_ground_truth()