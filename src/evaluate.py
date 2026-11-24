"""Step 7 (Test phase): score the pipeline against the hidden answer key."""
import pandas as pd
from src.pii import mask_pii


def evaluate(results, labels_path):
    labels = pd.read_csv(labels_path, dtype=str).set_index("id")
    rows = []
    for r in results:
        exp = labels.loc[r["id"]]
        exp_teams = set(exp["team"].split("|"))
        got_teams = set(r["teams"])
        rows.append({"ID": r["id"], "Expected team": exp["team"], "Got team": " | ".join(r["teams"]),
                     "Team correct": exp_teams == got_teams, "Expected priority": exp["priority"],
                     "Got priority": r["priority"], "Priority correct": exp["priority"] == r["priority"],
                     "Reason": r["reason"]})
    detail = pd.DataFrame(rows)
    n = len(detail)
    needs_review = sum("Needs Review" in r["teams"] for r in results)
    llm_calls = sum(r["llm_used"] for r in results)
    # Wrong-queue errors are costlier than review-queue errors:
    wrong_team = detail[(~detail["Team correct"]) & (detail["Got team"] != "Needs Review")]
    pii_leaks = sum(bool(mask_pii(r["llm_text"])[1]) for r in results if r["llm_text"])
    summary = pd.DataFrame([
        ("Messages evaluated", n, ""),
        ("Team routing accuracy", f"{detail['Team correct'].mean():.0%}", "target >= 90%"),
        ("Priority accuracy", f"{detail['Priority correct'].mean():.0%}", ""),
        ("Wrongly routed (confident but wrong)", len(wrong_team), "worst kind of error"),
        ("Sent to Needs Review", f"{needs_review} ({needs_review/n:.0%})", "target <= ~15%"),
        ("LLM calls made", f"{llm_calls} of {n}", "rules + empty skipped the rest"),
        ("Total tokens sent to LLM", sum(r["tokens"] for r in results), ""),
        ("PII reaching the LLM", pii_leaks, "target 0"),
        ("Spam auto-deleted", 0, "target 0 (nothing is ever deleted)"),
    ], columns=["Metric", "Value", "Note"])
    return summary, detail
