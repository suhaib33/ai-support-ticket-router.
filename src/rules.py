"""Step 2: high-certainty rules. A wrong rule is worse than no rule, so be strict.
Anything ambiguous returns None and is left for the LLM."""
import re

SPAM_RULES = [
    ("out_of_office", re.compile(r"\b(out of office|automatic reply|auto[- ]?reply|autoreply)\b", re.I)),
    ("lottery_prize", re.compile(r"\byou(?:'ve| have)? won\b|\bclaim your prize\b", re.I)),
    ("job_application", re.compile(r"\bapply for the (?:post|position|role)\b|\bapplication for (?:the )?(?:post|position)\b|\bcv attached\b|\bfind my (?:cv|resume)\b", re.I)),
    ("seo_marketing", re.compile(r"\bgoogle ranking\b|\bpage 1 of google\b|\bseo (?:services|offer|package)\b|\bboost your (?:ranking|traffic)\b", re.I)),
]
# NOTE: "wrong company" mails (e.g. 'Where is my Amazon parcel?') have no safe rule:
# a real customer may mention Amazon. We leave them to the LLM / human review.

def rule_filter(text: str):
    """Return ("Spam", "rule:<name>") on a confident match, else None."""
    for name, pattern in SPAM_RULES:
        if pattern.search(text or ""):
            return "Spam", f"rule:{name}"
    return None
