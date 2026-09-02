import re
from datetime import datetime
from typing import Any

class DataNormalizer:
    """
    Cleans and standardizes financial data to ensure deterministic 
    matching rules work accurately.
    """

    @staticmethod
    def normalize_string(text: Any) -> str:
        if not text or not isinstance(text, str):
            return ""
        text = text.lower()
        text = re.sub(r'\b(llc|inc|corp|co|ltd)\b', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def normalize_amount(amount: Any) -> float:
        if amount is None:
            return 0.0
        if isinstance(amount, (int, float)):
            return float(amount)
        amount_str = str(amount)
        amount_str = re.sub(r'[^\d.-]', '', amount_str)
        try:
            return float(amount_str)
        except ValueError:
            return 0.0

    @staticmethod
    def normalize_date(date_val: Any) -> str:
        if not date_val:
            return ""
        if isinstance(date_val, datetime):
            return date_val.strftime("%Y-%m-%d")
        date_str = str(date_val).strip()
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y", "%Y%m%d"]
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str