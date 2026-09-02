from typing import List
from datetime import timedelta
from app.database.models import BankTransaction, LedgerEntry

class CandidateGenerator:
    def __init__(self, amount_tolerance: float = 15.0, date_tolerance_days: int = 5):
        self.amount_tolerance = amount_tolerance
        self.date_tolerance_days = date_tolerance_days

    def generate_candidates(self, bank_txn: BankTransaction, ledger_pool: List[LedgerEntry]) -> List[LedgerEntry]:
        """
        Filters the ledger pool to find plausible candidates for a single bank transaction.
        """
        candidates = []
        
        for ledger in ledger_pool:
            # 1. Currency must match (Hard constraint)
            if bank_txn.currency != ledger.currency:
                continue
                
            # 2. Amount must be within tolerance
            amount_diff = abs(bank_txn.amount - ledger.amount)
            if amount_diff > self.amount_tolerance:
                continue
                
            # 3. Date must be within tolerance (Ledger usually lags bank by a few days, or vice versa)
            date_diff = abs((bank_txn.transaction_date - ledger.entry_date).days)
            if date_diff > self.date_tolerance_days:
                continue
                
            candidates.append(ledger)
            
        return candidates