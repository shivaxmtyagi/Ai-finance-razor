import pandas as pd
import numpy as np
import json
import uuid
import random
from datetime import datetime, timedelta
from Faker import Faker
import argparse
import os

fake = Faker()

def generate_synthetic_data(num_records=150, output_dir="../data"):
    os.makedirs(output_dir, exist_ok=True)
    
    bank_data = []
    ledger_data = []
    invoice_data = []
    ground_truth = {}
    
    # Core variables for realistic variations
    vendors = [fake.company() for _ in range(num_records // 3)]
    cloud_vendors = ["Amazon Web Services", "Microsoft Azure", "Google Cloud", "DigitalOcean"]
    vendors.extend(cloud_vendors)
    
    for i in range(num_records):
        b_id = f"B{str(i).zfill(4)}"
        l_id = f"L{str(i).zfill(4)}"
        inv_id = f"INV{str(i).zfill(4)}"
        
        base_date = fake.date_between(start_date='-60d', end_date='today')
        base_amount = round(random.uniform(50.0, 15000.0), 2)
        base_vendor = random.choice(vendors)
        base_ref = str(uuid.uuid4())[:8].upper()
        
        # 1. Bank Record (Baseline)
        bank_desc = f"{base_vendor.upper()[:10]} {fake.bs()}"
        bank_data.append({
            "transaction_id": b_id,
            "transaction_date": base_date.strftime("%Y-%m-%d"),
            "description": bank_desc,
            "amount": base_amount,
            "currency": "USD",
            "reference": base_ref,
            "transaction_type": "DEBIT"
        })
        
        # Scenario Generation
        scenario = random.choices(
            ["EXACT", "FUZZY_DATE", "FUZZY_AMOUNT", "FUZZY_VENDOR", "MISSING_LEDGER", "DUPLICATE"], 
            weights=[40, 20, 10, 15, 10, 5], 
            k=1
        )[0]
        
        match_exists = True
        target_l_id = l_id
        
        l_date = base_date
        l_amount = base_amount
        l_vendor = base_vendor
        
        if scenario == "MISSING_LEDGER":
            match_exists = False
            target_l_id = None
            
        elif scenario == "EXACT":
            pass # Keep everything identical
            
        elif scenario == "FUZZY_DATE":
            # Ledger recorded 1-3 days later
            l_date = base_date + timedelta(days=random.randint(1, 3))
            
        elif scenario == "FUZZY_AMOUNT":
            # Transcription error (e.g., cent difference)
            l_amount = round(base_amount + random.choice([-0.90, 0.50, -10.0]), 2)
            
        elif scenario == "FUZZY_VENDOR":
            # Abbreviation or capitalization diff
            variations = [l_vendor.lower(), l_vendor.replace(" ", ""), l_vendor[:5] + " LLC"]
            l_vendor = random.choice(variations)
            
        elif scenario == "DUPLICATE":
            # Generate the legit one
            ledger_data.append({
                "ledger_id": target_l_id,
                "entry_date": l_date.strftime("%Y-%m-%d"),
                "vendor": l_vendor,
                "description": fake.catch_phrase(),
                "amount": l_amount,
                "currency": "USD",
                "reference": base_ref,
                "account": "Expenses",
                "debit": l_amount,
                "credit": 0.0
            })
            # Generate the duplicate
            dup_id = f"L_DUP_{str(i).zfill(4)}"
            ledger_data.append({
                "ledger_id": dup_id,
                "entry_date": l_date.strftime("%Y-%m-%d"),
                "vendor": l_vendor,
                "description": fake.catch_phrase(),
                "amount": l_amount,
                "currency": "USD",
                "reference": base_ref,
                "account": "Expenses",
                "debit": l_amount,
                "credit": 0.0
            })
            
        if match_exists and scenario != "DUPLICATE":
            ledger_data.append({
                "ledger_id": target_l_id,
                "entry_date": l_date.strftime("%Y-%m-%d"),
                "vendor": l_vendor,
                "description": fake.catch_phrase(),
                "amount": l_amount,
                "currency": "USD",
                "reference": base_ref,
                "account": "Expenses",
                "debit": l_amount,
                "credit": 0.0
            })
            
        # Invoice generation (for context)
        if match_exists:
            invoice_data.append({
                "invoice_id": inv_id,
                "invoice_date": (base_date - timedelta(days=15)).strftime("%Y-%m-%d"),
                "vendor": base_vendor,
                "description": fake.catch_phrase(),
                "invoice_amount": base_amount,
                "currency": "USD",
                "invoice_number": f"INV-{base_ref}",
                "due_date": base_date.strftime("%Y-%m-%d"),
                "status": "PAID"
            })
            
        # Write Ground Truth
        ground_truth[b_id] = {
            "correct_ledger_id": target_l_id,
            "match": match_exists,
            "scenario": scenario
        }

    # Export
    pd.DataFrame(bank_data).to_csv(f"{output_dir}/bank_transactions.csv", index=False)
    pd.DataFrame(ledger_data).to_csv(f"{output_dir}/ledger_entries.csv", index=False)
    pd.DataFrame(invoice_data).to_csv(f"{output_dir}/invoices.csv", index=False)
    
    with open(f"{output_dir}/ground_truth.json", "w") as f:
        json.dump(ground_truth, f, indent=4)
        
    print(f"✅ Generated {len(bank_data)} Bank Txns, {len(ledger_data)} Ledger Entries, {len(invoice_data)} Invoices.")
    print(f"✅ Ground truth hidden in {output_dir}/ground_truth.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=150, help="Number of records to generate")
    args = parser.parse_args()
    generate_synthetic_data(args.records)