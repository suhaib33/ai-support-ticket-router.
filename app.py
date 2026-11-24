"""Streamlit dashboard for the Northwind Ticket Router.

Run:  python -m streamlit run app.py
It calls the same pipeline as main.py and the API, so results are identical.
"""
import io
import os

import pandas as pd
import streamlit as st

from src.config import CONFIDENCE_THRESHOLD, INBOX_FILE, LABELS_FILE
from src.evaluate import evaluate
from src.load_clean import clean_inbox, load_inbox
from src.pipeline import get_classifier, process_message
from src.tickets import build_run_log, build_tickets, write_workbook
from src.token_guard import TokenBudget

st.set_page_config(page_title="Northwind Ticket Router", page_icon="🎫", layout="wide")

MOCK_LABEL = "Mock (offline, no API key)"
REAL_LABEL = "Real LLM (hosted)"
KEY_VARS = {"openai": "OPENAI_API_KEY", "gemini": "GOOGLE_API_KEY", "groq": "GROQ_API_KEY"}
DEFAULT_MODELS = {"openai": "gpt-4o-mini", "gemini": "gemini-2.0-flash", "groq": "llama-3.1-8b-instant"}

EXAMPLES = {
    "— pick an example —": ("", ""),
    "Billing, urgent, with phone + card": (
        "URGENT!!!", "I was charged twice for order 4540!! Card ending 4417. Call me on 9876543210"),
    "Two intents (Product + Sales)": (
        "Broken + bulk", "My blender broke, and I also want a bulk quote for 50 more of the newer model."),
    "Obvious spam (rule, no LLM)": (
        "Automatic reply: Out of office", "I am out of office until Monday with limited access to email."),
    "Rambling email (token guard)": (
        "Hello",
        "Hello team, hope you are doing well. " + "I have been a customer for 6 years and my family also buys from you. " * 6
        + "Anyway, I ordered a washing machine WM-77 and the display shows error E4. What does E4 mean?"),
    "Vague message (low confidence)": ("Hi", "hmm what"),
}

REASON_TEXT = {
    "empty_message": "The message body is empty, so a human should look at it. No LLM call was made.",
    "llm": "The LLM classified it with enough confidence.",
    "llm_spam": "The LLM judged it to be spam. It goes to Spam Review, never deleted.",
    "llm_unclear": "The LLM could not tell what this is, so a human reviews it.",
    "low_confidence": "The LLM was below the confidence threshold, so a human reviews it.",
    "llm_error": "The LLM call failed after retries, so a human reviews it.",
    "token_budget_exceeded": "The run's token budget was used up, so the LLM was skipped.",
}


def explain_reason(reason: str) -> str:
    if reason.startswith("rule:"):
        return f"A free rule ({reason[5:]}) matched with high certainty, so the LLM was skipped."
    return REASON_TEXT.get(reason, reason)


# ------------------------------------------------------------------ sidebar
def sidebar_settings() -> dict:
    st.sidebar.header("Settings")
    mode = st.sidebar.radio("Classifier", [MOCK_LABEL, REAL_LABEL])
    s = {"mode": mode, "provider": "openai", "model": "", "api_key": ""}
    if mode == REAL_LABEL:
        s["provider"] = st.sidebar.selectbox("Provider", list(KEY_VARS))
        s["model"] = st.sidebar.text_input("Model", value=DEFAULT_MODELS[s["provider"]])
        s["api_key"] = st.sidebar.text_input(f"API key ({KEY_VARS[s['provider']]})", type="password")
        st.sidebar.warning(
            "Masked customer text leaves your machine in this mode. Names are NOT masked. "
            "Get IT approval before using real customer data.")
    s["threshold"] = st.sidebar.slider("Confidence threshold", 0.0, 1.0, float(CONFIDENCE_THRESHOLD), 0.05,
                                       help="Below this, the message goes to Needs Review.")
    s["budget"] = st.sidebar.number_input("Token budget per run", min_value=50, max_value=100000,
                                          value=5000, step=50,
                                          help="When used up, remaining messages skip the LLM and go to Needs Review.")
    st.sidebar.caption("Rules, PII masking and the token guard always run before the LLM.")
    return s


def make_classifier(s: dict):
    """Build a classifier from the sidebar settings. Keys stay in this process only."""
    if s["mode"] == MOCK_LABEL:
        os.environ["USE_MOCK"] = "1"
    else:
        os.environ["USE_MOCK"] = "0"
        os.environ["LLM_PROVIDER"] = s["provider"]
        if s["model"]:
            os.environ["LLM_MODEL"] = s["model"]
        if s["api_key"]:
            os.environ[KEY_VARS[s["provider"]]] = s["api_key"]
    return get_classifier()


def trace_steps(r: dict) -> list:
    """Human-readable list of what happened, in pipeline order."""
    steps = ["Cleaned the text (whitespace, subject + message combined)."]
    if r["reason"] == "empty_message":
        return steps + ["Message is empty, so it was sent to Needs Review."]
    if r["reason"].startswith("rule:"):
        return steps + [f"Rule matched: {r['reason'][5:]}. LLM skipped, no cost."]
    steps.append("No spam rule matched.")
    pii = ", ".join(f"{v} {k}" for k, v in r["pii_counts"].items())
    steps.append(f"Masked personal data: {pii}." if pii else "No personal data found to mask.")
    steps.append(f"Token guard: {r['tokens']} tokens" + (" (budget exceeded, LLM skipped)." if r["reason"] == "token_budget_exceeded" else "."))
    if r["llm_used"]:
        if r["reason"] == "llm_error":
            steps.append(f"LLM call failed: {r['error']}")
        else:
            steps.append(f"LLM answered with confidence {r['confidence']:.2f}.")
    steps.append("Final routing: " + " + ".join(r["teams"]) + ".")
    return steps


# ------------------------------------------------------------------ tab 1
def tab_try_one(s: dict):
    st.subheader("Route one message")

    def load_example():
        subj, msg = EXAMPLES[st.session_state["example"]]
        st.session_state["subject"], st.session_state["message"] = subj, msg

    st.selectbox("Quick examples", list(EXAMPLES), key="example", on_change=load_example)
    st.text_input("Subject (optional)", key="subject")
    st.text_area("Customer message", key="message", height=130)

    if st.button("Route it", type="primary", key="route_one"):
        subject = " ".join(st.session_state.get("subject", "").split())
        message = " ".join(st.session_state.get("message", "").split())
        text = f"{subject}. {message}".strip(" .")
        try:
            r = process_message("demo", text, is_empty=(message == ""), classifier=make_classifier(s),
                                budget=TokenBudget(total=int(s["budget"])), threshold=s["threshold"])
        except Exception as e:  # e.g. missing langchain package or bad key
            st.error(f"Could not run the classifier: {type(e).__name__}: {e}")
            return

        if r["teams"] == ["Needs Review"]:
            st.warning("Routed to: **Needs Review** (a human decides)")
        elif r["teams"] == ["Spam Review"]:
            st.info("Routed to: **Spam Review** (never auto-deleted)")
        else:
            st.success("Routed to: **" + "  +  ".join(r["teams"]) + "**" + ("  (2 tickets)" if len(r["teams"]) > 1 else ""))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Priority", r["priority"])
        c2.metric("Confidence", "n/a" if r["confidence"] is None else f"{r['confidence']:.2f}")
        c3.metric("Tokens sent", r["tokens"])
        c4.metric("PII items masked", sum(r["pii_counts"].values()))

        st.write("**Why:** " + explain_reason(r["reason"]))
        if r["summary"]:
            st.write("**Ticket summary:** " + r["summary"])
        with st.expander("What the LLM actually saw (after masking and trimming)", expanded=bool(r["llm_text"])):
            st.code(r["llm_text"] or "(The LLM was not called for this message.)", language=None)
        with st.expander("Pipeline trace"):
            for i, step in enumerate(trace_steps(r), 1):
                st.write(f"{i}. {step}")


# ------------------------------------------------------------------ tab 2
def run_batch_ui(s: dict, source) -> dict:
    raw = load_inbox(source)
    clean, issues = clean_inbox(raw)
    classifier, budget = make_classifier(s), TokenBudget(total=int(s["budget"]))
    results, bar = [], st.progress(0.0, text="Processing messages...")
    for i, (_, row) in enumerate(clean.iterrows(), 1):
        results.append(process_message(row["ID"], row["text"], bool(row["is_empty"]), classifier, budget, s["threshold"]))
        bar.progress(i / len(clean), text=f"Processed {i} of {len(clean)}")
    bar.empty()

    tickets, run_log = build_tickets(results, clean), build_run_log(results)
    sheets = {"Tickets": tickets, "Run Log": run_log, "Issues": issues}
    summary = detail = None
    if source is INBOX_FILE:                       # only the sample has an answer key
        summary, detail = evaluate(results, LABELS_FILE)
        sheets.update({"Evaluation": summary, "Eval Detail": detail})
    buf = io.BytesIO()
    write_workbook(buf, sheets)
    return {"raw_n": len(raw), "clean_n": len(clean), "results": results, "tickets": tickets, "run_log": run_log,
            "issues": issues, "summary": summary, "detail": detail, "xlsx": buf.getvalue()}


def tab_batch(s: dict):
    st.subheader("Process an inbox export")
    src = st.radio("Source", ["Sample inbox (24 messy emails)", "Upload Excel"], horizontal=True, key="src")
    upload = None
    if src == "Upload Excel":
        upload = st.file_uploader("Excel with columns: ID, Received At, Customer Email, Subject, Message", type=["xlsx"])

    if st.button("Run pipeline", type="primary", key="run_batch"):
        if src == "Upload Excel" and upload is None:
            st.error("Please upload an .xlsx file first.")
        else:
            try:
                st.session_state["batch"] = run_batch_ui(s, INBOX_FILE if src.startswith("Sample") else upload)
            except Exception as e:
                st.session_state.pop("batch", None)
                st.error(f"{type(e).__name__}: {e}")

    b = st.session_state.get("batch")
    if not b:
        st.caption("Pick a source and press **Run pipeline**.")
        return

    res = b["results"]
    review = sum("Needs Review" in r["teams"] for r in res)
    m = st.columns(6)
    m[0].metric("Rows loaded", b["raw_n"])
    m[1].metric("After cleaning", b["clean_n"])
    m[2].metric("Tickets created", len(b["tickets"]))
    m[3].metric("LLM calls", sum(r["llm_used"] for r in res))
    m[4].metric("Needs Review", f"{review} ({review / max(1, len(res)):.0%})")
    m[5].metric("PII masked", sum(sum(r["pii_counts"].values()) for r in res))

    left, right = st.columns([1, 2])
    with left:
        st.write("**Tickets per team**")
        st.bar_chart(b["tickets"]["Assigned Team"].value_counts())
    with right:
        st.write("**Tickets**")
        teams = sorted(b["tickets"]["Assigned Team"].unique())
        picked = st.multiselect("Filter by team", teams, default=teams)
        st.dataframe(b["tickets"][b["tickets"]["Assigned Team"].isin(picked)], hide_index=True, width="stretch")

    t_log, t_issues, t_eval = st.tabs(["Run log", "Data issues", "Evaluation"])
    with t_log:
        st.dataframe(b["run_log"], hide_index=True, width="stretch")
    with t_issues:
        st.dataframe(b["issues"], hide_index=True, width="stretch")
    with t_eval:
        if b["summary"] is None:
            st.info("Evaluation needs an answer key, which only the sample inbox has.")
        else:
            st.dataframe(b["summary"], hide_index=True, width="stretch")
            st.write("**Messages not routed as expected**")
            st.dataframe(b["detail"][~b["detail"]["Team correct"]], hide_index=True, width="stretch")

    st.download_button("Download tickets.xlsx", data=b["xlsx"], file_name="tickets.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ------------------------------------------------------------------ tab 3
def tab_how():
    st.subheader("How the pipeline works")
    st.markdown(
        """
| # | Step | Why it is there |
|---|---|---|
| 1 | **Clean and deduplicate** | Avoids paying for the same email twice; empty messages are flagged, not dropped |
| 2 | **Rules** | Obvious spam is caught for free, so the LLM is skipped |
| 3 | **PII masking** | Phones, emails and card digits never reach the LLM |
| 4 | **Token guard** | Trims long emails (keeping the end), enforces a budget |
| 5 | **LLM classification** | Validated output: categories, priority, summary, confidence |
| 6 | **Confidence check** | Unsure, failed or over-budget cases go to **Needs Review** |
| 7 | **Tickets** | One ticket per team, so a two-intent message becomes two tickets |

**Safety rules:** nothing is auto-deleted (junk goes to Spam Review), and a failed or uncertain LLM call
never causes a lost message.
"""
    )


def main():
    st.title("🎫 Northwind Ticket Router")
    st.caption("Support emails in, tickets for the right team out. Built phase by phase as an FDE practice project.")
    s = sidebar_settings()
    t1, t2, t3 = st.tabs(["Try one message", "Process inbox", "How it works"])
    with t1:
        tab_try_one(s)
    with t2:
        tab_batch(s)
    with t3:
        tab_how()


main()