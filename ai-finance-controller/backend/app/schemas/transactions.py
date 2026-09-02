from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class BankTransactionBase(BaseModel):
    transaction_id: str = Field(..., description="Unique ID for the bank transaction")
    transaction_date: date
    description: str
    amount: float
    currency: str = Field(default="USD")
    reference: Optional[str] = None
    transaction_type: str

class LedgerEntryBase(BaseModel):
    ledger_id: str = Field(..., description="Unique ID for the ledger entry")
    entry_date: date
    vendor: str
    description: str
    amount: float
    currency: str = Field(default="USD")
    reference: Optional[str] = None
    account: Optional[str] = None
    debit: Optional[float] = 0.0
    credit: Optional[float] = 0.0

class InvoiceBase(BaseModel):
    invoice_id: str
    invoice_date: date
    vendor: str
    description: str
    invoice_amount: float
    currency: str = Field(default="USD")
    invoice_number: str
    due_date: date
    status: str

class NormalizationResult(BaseModel):
    original_id: str
    normalized_text: str
    normalized_amount: float
    normalized_date: date