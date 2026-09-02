from rapidfuzz import fuzz
from typing import Dict, Any
from app.database.models import BankTransaction, LedgerEntry

class RuleMatcher:
    """
    Computes a deterministic confidence score based on exact and fuzzy business rules.
    """
    
    @staticmethod
    def calculate_confidence(bank: BankTransaction, ledger: LedgerEntry) -> Dict[str, Any]:
        score = 0.0
        evidence = []
        
        # 1. Amount Scoring (Max 40 points)
        amount_diff = abs(bank.amount - ledger.amount)
        if amount_diff == 0:
            score += 0.40
            evidence.append("Amount matches exactly")
        elif amount_diff <= 1.0:
            score += 0.20
            evidence.append(f"Amount within $1.00 tolerance (Diff: ${amount_diff:.2f})")
            
        # 2. Date Scoring (Max 20 points)
        date_diff = abs((bank.transaction_date - ledger.entry_date).days)
        if date_diff == 0:
            score += 0.20
            evidence.append("Date matches exactly")
        elif date_diff <= 2:
            score += 0.10
            evidence.append(f"Date within 2 days (Diff: {date_diff} days)")

        # 3. Reference Matching (Max 20 points)
        if bank.reference and ledger.reference and bank.reference == ledger.reference:
            score += 0.20
            evidence.append("Reference ID matches exactly")
            
        # 4. Fuzzy Vendor/Description Scoring (Max 20 points)
        # Using RapidFuzz token sort ratio to handle out-of-order words (e.g., "AWS Cloud" vs "Cloud AWS")
        vendor_sim = fuzz.token_sort_ratio(bank.description, ledger.vendor) / 100.0
        desc_sim = fuzz.token_sort_ratio(bank.description, ledger.description) / 100.0
        
        best_text_sim = max(vendor_sim, desc_sim)
        if best_text_sim > 0.85:
            score += 0.20
            evidence.append(f"High text similarity ({int(best_text_sim*100)}%)")
        elif best_text_sim > 0.60:
            score += 0.10
            evidence.append(f"Moderate text similarity ({int(best_text_sim*100)}%)")

        return {
            "confidence_score": round(score, 2),
            "match_method": "RULE_BASED",
            "evidence": evidence,
            "metrics": {
                "amount_diff": amount_diff,
                "date_diff_days": date_diff,
                "vendor_similarity": vendor_sim,
                "desc_similarity": desc_sim
            }
        }