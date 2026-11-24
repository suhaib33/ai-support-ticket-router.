import logging
from src.config import INBOX_FILE, LABELS_FILE, OUTPUT_DIR
from src.load_clean import load_inbox, clean_inbox
from src.pipeline import run_batch
from src.tickets import build_tickets, build_run_log, write_workbook
from src.evaluate import evaluate

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    clean, issues = clean_inbox(load_inbox(INBOX_FILE))
    results = run_batch(clean)
    tickets = build_tickets(results, clean)
    summary, detail = evaluate(results, LABELS_FILE)
    out = OUTPUT_DIR / "tickets.xlsx"
    write_workbook(out, {"Tickets": tickets, "Run Log": build_run_log(results), "Issues": issues,
                         "Evaluation": summary, "Eval Detail": detail})
    print(summary.to_string(index=False))
    print("\nWrong or review cases:")
    print(detail[~detail["Team correct"]].to_string(index=False))
    print(f"\nTickets created: {len(tickets)}  ->  {out}")
