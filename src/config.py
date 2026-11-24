"""Central settings. Change values here, not inside the logic."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INBOX_FILE = BASE_DIR / "data" / "support_inbox.xlsx"
LABELS_FILE = BASE_DIR / "data" / "expected_labels.csv"
OUTPUT_DIR = BASE_DIR / "output"

REQUIRED_COLUMNS = ["ID", "Received At", "Customer Email", "Subject", "Message"]

CATEGORY_TO_TEAM = {
    "Sales": "Sales", "Product": "Product", "Billing": "Finance",
    "IT": "IT", "General": "Support",
    "Spam": "Spam Review",       # never auto-deleted
    "Unclear": "Needs Review",   # low confidence -> human
}
CONFIDENCE_THRESHOLD = 0.7
