"""Step 6: turn routing results into ticket rows and an Excel workbook."""
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


def build_tickets(results, clean_df) -> pd.DataFrame:
    src = clean_df.set_index("ID")
    rows, n = [], 0
    for r in results:
        s = src.loc[r["id"]]
        for team in r["teams"]:
            n += 1
            rows.append({
                "Ticket ID": f"TKT-{n:04d}", "Source ID": r["id"],
                "Customer Email": s["Customer Email"], "Original Message": s["text"],
                "Assigned Team": team, "Priority": r["priority"], "Summary": r["summary"],
                "Confidence": r["confidence"], "Route Reason": r["reason"],
                "Status": "New",
            })
    return pd.DataFrame(rows)


def build_run_log(results) -> pd.DataFrame:
    return pd.DataFrame([{
        "ID": r["id"], "Teams": " | ".join(r["teams"]), "Reason": r["reason"], "LLM used": r["llm_used"],
        "Tokens": r["tokens"], "PII masked": sum(r["pii_counts"].values()), "Confidence": r["confidence"], "Error": r["error"],
    } for r in results])


def write_workbook(path, sheets: dict):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            for c in ws[1]:
                c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F4E78")
            for i, col in enumerate(df.columns, 1):
                width = min(60, max(len(str(col)), *(len(str(v)) for v in df[col])) + 2) if len(df) else len(str(col)) + 2
                ws.column_dimensions[get_column_letter(i)].width = width
                for cell in ws[get_column_letter(i)][1:]:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")
            ws.freeze_panes = "A2"
