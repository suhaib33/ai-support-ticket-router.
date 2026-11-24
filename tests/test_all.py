import pandas as pd
from fastapi.testclient import TestClient
from src.load_clean import clean_inbox
from src.rules import rule_filter
from src.pii import mask_pii
from src.token_guard import TokenBudget, trim_to_limit, strip_noise, count_tokens
from src.pipeline import process_message
from src.llm_classifier import Classifier, MockClassifier
from src.schemas import Classification
from src.api import app


def mk(rows):
    return pd.DataFrame(rows, columns=["ID", "Received At", "Customer Email", "Subject", "Message"])

# ---- Step 1: cleaning
def test_duplicates_removed_case_and_space_insensitive():
    clean, issues = clean_inbox(mk([["1", "2026-11-24 09:00", "a@x.com", "Hi", "Need help"],
                                    ["2", "2026-11-24 09:05", "  A@X.com ", "Hi", "need   help"]]))
    assert len(clean) == 1 and issues.iloc[0]["ID"] == "2"

def test_same_message_different_customers_both_kept():
    clean, _ = clean_inbox(mk([["1", "2026-11-24 09:00", "a@x.com", "", "Where is my order?"],
                               ["2", "2026-11-24 09:01", "b@x.com", "", "Where is my order?"]]))
    assert len(clean) == 2

def test_empty_message_flagged_not_dropped():
    clean, issues = clean_inbox(mk([["1", "2026-11-24 09:00", "a@x.com", "???", None]]))
    assert len(clean) == 1 and bool(clean.loc[0, "is_empty"])

# ---- Step 2: rules (spam caught, real customers untouched)
def test_rules_catch_spam():
    for t in ["Automatic reply: Out of office", "YOU WON $1,000,000", "I wish to apply for the post of Analyst",
              "We can boost your Google ranking"]:
        assert rule_filter(t) and rule_filter(t)[0] == "Spam"

def test_rules_never_touch_real_customers():
    for t in ["Bulk order. I want a bulk discount", "URGENT!!!. charged twice", "Is the store open on Sunday?",
              "what is your return policy", "Where is my Amazon parcel?", "Is delivery free?"]:
        assert rule_filter(t) is None

# ---- Step 3: PII
def test_pii_masked_and_order_numbers_kept():
    t, c = mask_pii("charged twice order 4540!! Card ending 4417. My number is 9876543210")
    assert "4417" not in t and "9876543210" not in t and "4540" in t and c == {"CARD": 1, "PHONE": 1}
    t, c = mask_pii("Call me on +91 98450 11223. order 4560")
    assert "[PHONE]" in t and "4560" in t
    assert mask_pii("mail rahul.m@gmail.com")[0] == "mail [EMAIL]"

def test_long_order_number_not_a_phone():
    assert mask_pii("order 4540123456")[1] == {}

# ---- Step 4: token guard
def test_trim_keeps_last_sentence_and_short_unchanged():
    long = "Blah blah. " * 80 + "What does error E4 mean?"
    out = trim_to_limit(long, 40)
    assert out.endswith("What does error E4 mean?") and count_tokens(out) <= 45
    assert trim_to_limit("short text", 40) == "short text"

def test_strip_noise_and_budget_blocks():
    assert strip_noise("Need refund.\n> old quote\nRegards,\nRahul") == "Need refund."
    b = TokenBudget(total=100)
    flags = [b.guard("x" * 160)[2] for _ in range(4)]
    assert flags == [True, True, False, False]

# ---- Step 5/6: pipeline decisions
def run(text, empty=False, llm=None, budget=None):
    return process_message("1", text, empty, Classifier(llm=llm or MockClassifier(), backoff=0), budget or TokenBudget())

def test_empty_goes_to_review_without_llm():
    r = run("???", empty=True)
    assert r["teams"] == ["Needs Review"] and not r["llm_used"]

def test_rule_spam_skips_llm_and_goes_to_spam_review():
    r = run("Automatic reply: Out of office")
    assert r["teams"] == ["Spam Review"] and not r["llm_used"] and r["tokens"] == 0

def test_multi_intent_makes_two_teams():
    r = run("My blender broke, and I also want a bulk quote for 50 more")
    assert set(r["teams"]) == {"Product", "Sales"}

def test_pii_never_reaches_llm():
    r = run("I was charged twice. Card ending 4417. Call 9876543210")
    assert r["teams"] == ["Finance"] and not mask_pii(r["llm_text"])[1]

def test_low_confidence_goes_to_review():
    assert run("hmm what")["teams"] == ["Needs Review"]

def test_llm_failure_goes_to_review():
    class Dead:
        def invoke(self, m): raise TimeoutError("down")
    r = run("charged twice", llm=Dead())
    assert r["teams"] == ["Needs Review"] and r["reason"] == "llm_error"

def test_budget_exhausted_goes_to_review():
    r = run("I was charged twice for my order", budget=TokenBudget(total=1))
    assert r["teams"] == ["Needs Review"] and r["reason"] == "token_budget_exceeded"

def test_schema_rejects_bad_output():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Classification(categories=["Cooking"], priority="High", summary="x", confidence=0.5)
    with pytest.raises(ValidationError):
        Classification(categories=["IT"], priority="High", summary="x", confidence=1.7)

# ---- Deploy: API
client = TestClient(app)

def test_api_health_and_route():
    assert client.get("/health").json() == {"status": "ok"}
    r = client.post("/route", json={"subject": "Invoice", "message": "Where can I download my invoice for order 4533?"})
    assert r.status_code == 200 and r.json()["teams"] == ["Finance"]

def test_api_validation_rejects_huge_message():
    assert client.post("/route", json={"message": "x" * 6000}).status_code == 422

def test_api_batch():
    r = client.post("/route-batch", json=[{"id": "a", "message": "Out of office"}, {"id": "b", "message": "demo of enterprise plan"}])
    assert [x["teams"] for x in r.json()] == [["Spam Review"], ["Sales"]]
