from .invoice import InvoiceTemplate
from .receipt import ReceiptTemplate
from .contract import ContractTemplate
from .resume import ResumeTemplate
from .purchase_order import PurchaseOrderTemplate
from .bank_statement import BankStatementTemplate

DOCUMENT_TEMPLATES = {
    "invoice": InvoiceTemplate(),
    "receipt": ReceiptTemplate(),
    "contract": ContractTemplate(),
    "resume": ResumeTemplate(),
    "purchase_order": PurchaseOrderTemplate(),
    "bank_statement": BankStatementTemplate(),
}

__all__ = [
    "InvoiceTemplate",
    "ReceiptTemplate",
    "ContractTemplate",
    "ResumeTemplate",
    "PurchaseOrderTemplate",
    "BankStatementTemplate",
    "DOCUMENT_TEMPLATES",
]