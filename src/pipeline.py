"""Wires all steps together for ONE message.
clean row -> rules -> PII mask -> token guard -> LLM -> confidence check -> teams"""
import os
from src.config import CATEGORY_TO_TEAM, CONFIDENCE_THRESHOLD
from src.rules import rule_filter
from src.pii import mask_pii
from src.token_guard import TokenBudget
from src.llm_classifier import Classifier, MockClassifier


def get_classifier() -> Classifier:
    """USE_MOCK=1 (default) -> offline mock. USE_MOCK=0 -> real provider via LLM_PROVIDER."""
    if os.getenv("USE_MOCK", "1") == "1":
        return Classifier(llm=MockClassifier(), backoff=0)
    return Classifier()


def _result(msg_id, teams, reason, **extra):
    base = dict(id=str(msg_id), teams=teams, reason=reason, priority="Low", summary="",
                confidence=None, tokens=0, pii_counts={}, llm_text="", llm_used=False, error=None)
    base.update(extra)
    return base


def process_message(msg_id, text: str, is_empty: bool, classifier: Classifier, budget: TokenBudget,
                    threshold: float = None) -> dict:
    # `threshold` lets callers (e.g. the Streamlit UI) override the confidence cut-off per run.
    threshold = CONFIDENCE_THRESHOLD if threshold is None else threshold

    if is_empty or not text.strip():
        return _result(msg_id, ["Needs Review"], "empty_message")

    hit = rule_filter(text)
    if hit:
        category, reason = hit
        return _result(msg_id, [CATEGORY_TO_TEAM[category]], reason, summary="Matched a spam rule")

    masked, pii_counts = mask_pii(text)
    guarded, tokens, allowed = budget.guard(masked)
    if not allowed:
        return _result(msg_id, ["Needs Review"], "token_budget_exceeded", tokens=tokens, pii_counts=pii_counts, llm_text=guarded)

    res, err = classifier.classify(guarded)
    common = dict(tokens=tokens, pii_counts=pii_counts, llm_text=guarded, llm_used=True)
    if res is None:
        return _result(msg_id, ["Needs Review"], "llm_error", error=err, **common)

    common.update(priority=res.priority, summary=res.summary, confidence=res.confidence)

    if res.confidence < threshold:
        return _result(msg_id, ["Needs Review"], "low_confidence", **common)
    if "Unclear" in res.categories:
        return _result(msg_id, ["Needs Review"], "llm_unclear", **common)

    teams = []
    for c in res.categories:
        t = CATEGORY_TO_TEAM[c]
        if t not in teams:
            teams.append(t)
    reason = "llm_spam" if teams == ["Spam Review"] else "llm"
    return _result(msg_id, teams, reason, **common)


def run_batch(clean_df, classifier=None, budget=None, threshold=None):
    classifier = classifier or get_classifier()
    budget = budget or TokenBudget()
    return [process_message(r["ID"], r["text"], bool(r["is_empty"]), classifier, budget, threshold)
            for _, r in clean_df.iterrows()]