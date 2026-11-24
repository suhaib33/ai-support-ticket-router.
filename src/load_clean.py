"""Step 1: read the Excel export, clean it, remove duplicates."""
import logging, re
import pandas as pd
from src.config import REQUIRED_COLUMNS

log = logging.getLogger(__name__)

def load_inbox(path) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Inbox file is missing columns: {missing}")
    log.info("Loaded %d raw rows", len(df))
    return df

def _normalize_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()

def clean_inbox(df: pd.DataFrame):
    """Return (clean_df, issues). `issues` lists rows set aside and why."""
    df = df.copy()
    issues = []
    for col in ["Subject", "Message"]:
        df[col] = df[col].map(_normalize_text)
    df["Customer Email"] = df["Customer Email"].map(_normalize_text).str.lower()
    df["Received At"] = pd.to_datetime(df["Received At"], errors="coerce")
    df["text"] = (df["Subject"] + ". " + df["Message"]).str.strip(" .")
    empty = df["Message"] == ""
    for _, r in df[empty].iterrows():
        issues.append({"ID": r["ID"], "issue": "empty message (kept, sent to Needs Review)"})
    df["is_empty"] = empty
    key = df["Customer Email"] + "||" + df["Message"].str.lower()
    dup = key.duplicated(keep="first") & ~empty
    for _, r in df[dup].iterrows():
        issues.append({"ID": r["ID"], "issue": "duplicate of an earlier message (removed)"})
    clean = df[~dup].reset_index(drop=True)
    log.info("Clean rows: %d | duplicates removed: %d | empty flagged: %d", len(clean), int(dup.sum()), int(empty.sum()))
    return clean, pd.DataFrame(issues, columns=["ID", "issue"])
