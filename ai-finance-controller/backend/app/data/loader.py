import pandas as pd
import uuid
from typing import Tuple
from sqlalchemy.orm import Session
from app.database.models import ReconciliationRun, BankTransaction, LedgerEntry
from app.schemas.transactions import BankTransactionBase, LedgerEntryBase
from app.data.normalizer import DataNormalizer

class DataLoader:
    def __init__(self, db: Session):
        self.db = db

    def load_reconciliation_files(self, bank_csv_path: str, ledger_csv_path: str) -> str:
        """
        Reads CSVs, validates, normalizes, and loads them into the database.
        Returns the run_id.
        """
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        
        # Create the run record
        run = ReconciliationRun(id=run_id, status="DATA_LOADED")
        self.db.add(run)
        
        # Load CSVs
        bank_df = pd.read_csv(bank_csv_path).fillna("")
        ledger_df = pd.read_csv(ledger_csv_path).fillna("")
        
        bank_records_processed = 0
        ledger_records_processed = 0

        # Process Bank Transactions
        for _, row in bank_df.iterrows():
            try:
                # Validate with Pydantic
                valid_data = BankTransactionBase(**row.to_dict())
                
                # Normalize and save
                db_record = BankTransaction(
                    transaction_id=valid_data.transaction_id,
                    run_id=run_id,
                    transaction_date=valid_data.transaction_date,
                    description=DataNormalizer.normalize_string(valid_data.description),
                    amount=DataNormalizer.normalize_amount(valid_data.amount),
                    currency=valid_data.currency,
                    reference=DataNormalizer.normalize_string(valid_data.reference),
                    transaction_type=valid_data.transaction_type
                )
                self.db.add(db_record)
                bank_records_processed += 1
            except Exception as e:
                print(f"Skipping malformed bank row {row.get('transaction_id')}: {e}")

        # Process Ledger Entries
        for _, row in ledger_df.iterrows():
            try:
                valid_data = LedgerEntryBase(**row.to_dict())
                
                db_record = LedgerEntry(
                    ledger_id=valid_data.ledger_id,
                    run_id=run_id,
                    entry_date=valid_data.entry_date,
                    vendor=DataNormalizer.normalize_string(valid_data.vendor),
                    description=DataNormalizer.normalize_string(valid_data.description),
                    amount=DataNormalizer.normalize_amount(valid_data.amount),
                    currency=valid_data.currency,
                    reference=DataNormalizer.normalize_string(valid_data.reference),
                    account=valid_data.account
                )
                self.db.add(db_record)
                ledger_records_processed += 1
            except Exception as e:
                print(f"Skipping malformed ledger row {row.get('ledger_id')}: {e}")

        run.total_records = bank_records_processed + ledger_records_processed
        self.db.commit()
        
        return run_id