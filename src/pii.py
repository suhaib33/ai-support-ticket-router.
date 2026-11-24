"""Step 3: mask personal data BEFORE any text is sent to an LLM."""
import re

# Order matters: mask the most specific patterns first.
PII_RULES = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("CARD",  re.compile(r"(?i)\b(?:card|visa|mastercard|debit|credit)\b[^.\d]{0,25}\d{4}\b")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")),
]

def mask_pii(text: str):
    """Return (masked_text, counts). Order numbers are kept on purpose."""
    counts = {}
    for label, pattern in PII_RULES:
        text, n = pattern.subn(f"[{label}]", text)
        if n:
            counts[label] = n
    return text, counts
