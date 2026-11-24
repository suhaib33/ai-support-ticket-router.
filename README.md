# 🎫 AI Support Ticket Router

> Reads messy customer support emails, decides which team should handle each one, protects private data, keeps AI costs under control, and creates a ticket for the right team. When it is unsure, it hands the message to a human instead of guessing.

This is a practice project built phase by phase the way a **Forward Deployed Engineer (FDE)** would build it for a real customer: **Discover → Define → Design → Build → Deploy → Test**.

---

## Table of contents

1. [What is this, in plain words?](#1-what-is-this-in-plain-words)
2. [The story behind it](#2-the-story-behind-it)
3. [What it does, step by step](#3-what-it-does-step-by-step)
4. [Quick start (about 10 minutes)](#4-quick-start-about-10-minutes)
5. [Using the Streamlit app](#5-using-the-streamlit-app)
6. [Using the command line](#6-using-the-command-line)
7. [Using the API](#7-using-the-api)
8. [Sending tickets by email (optional)](#8-sending-tickets-by-email-optional)
9. [Using a real AI model instead of the mock (optional)](#9-using-a-real-ai-model-instead-of-the-mock-optional)
10. [Project structure: what every file does](#10-project-structure-what-every-file-does)
11. [The sample data](#11-the-sample-data)
12. [How a message is routed](#12-how-a-message-is-routed)
13. [Safety features](#13-safety-features)
14. [Settings reference](#14-settings-reference)
15. [Running the tests](#15-running-the-tests)
16. [Docker (optional)](#16-docker-optional)
17. [Troubleshooting](#17-troubleshooting)
18. [Honest limits of this project](#18-honest-limits-of-this-project)
19. [Ideas for next steps](#19-ideas-for-next-steps)
20. [Glossary](#20-glossary)

---

## 1. What is this, in plain words?

Imagine a company called **Northwind Retail**. Customers email one shared support inbox all day. A person reads each email, decides who should deal with it, and forwards it:

- "I want a bulk discount for 200 laptops" → the **Sales** team
- "My blender stopped working" → the **Product** team
- "I was charged twice" → the **Finance** team
- "Your website keeps crashing" → the **IT** team
- "Is the store open on Sunday?" → the **Support** team
- Junk mail, job applications, out-of-office replies → **should not reach any team**

With 150 to 200 emails a day, this takes hours and mistakes happen (about 1 in 10 emails goes to the wrong team).

**This project does that sorting automatically.** It reads an Excel export of the inbox and produces a list of tickets, one per team, with a priority and a one-line summary. Anything it is not sure about goes to a **human review queue**, so no customer is ever lost.

---

## 2. The story behind it

The project follows the six phases an FDE goes through with a customer.

| Phase | What happened |
|---|---|
| **1. Discover** | We "interviewed" the customer (Priya, the Support Lead). We learned that the data is messy, that there is a Finance team nobody mentioned at first, and that junk mail must never be deleted automatically. |
| **2. Define** | We wrote down the problem, what is in scope for version 1, and measurable targets: 90% or better routing accuracy, no private data sent to the AI, and no auto-deleted mail. |
| **3. Design** | We chose the order of the steps: cheap checks first, the expensive AI last. |
| **4. Build** | We wrote the code, one module per step. |
| **5. Deploy** | We wrapped it in a web dashboard (Streamlit), a web API (FastAPI) and a Dockerfile. |
| **6. Test** | We wrote automated tests and scored the results against a hidden answer key. |

---

## 3. What it does, step by step

Every email goes through the same pipeline. Cheap and certain checks run first. The expensive AI call runs last, and only if it is really needed.

```
 Excel inbox
     │
     ▼
 ① CLEAN        Fix spaces, remove duplicates, flag empty messages
     │
     ▼
 ② RULES        Obvious spam (out-of-office, lottery, job applications) → Spam Review.
     │          No AI needed, so this step is free.
     ▼
 ③ PII MASK     Hide phone numbers, emails, card numbers → [PHONE] [EMAIL] [CARD]
     │
     ▼
 ④ TOKEN GUARD  Trim very long emails (keeping the end), enforce a spending budget
     │
     ▼
 ⑤ AI MODEL     Reads the masked text and answers in a strict format:
     │          category, priority, one-line summary, confidence
     ▼
 ⑥ CONFIDENCE   Not sure? Failed? Over budget? → Needs Review (a human)
     │
     ▼
 ⑦ TICKETS      One ticket per team. A message with two requests makes two tickets.
     │
     ▼
 Excel file  ·  dashboard tables  ·  optional email to each team
```

### Why this order?

| Rule of thumb | Reason |
|---|---|
| Clean first | You should not pay the AI twice for the same email. |
| Rules before the AI | Anything a simple rule can decide is free and certain. |
| Mask private data before the AI | Customer phone numbers and card digits never leave your computer. |
| Guard tokens before the AI | A single giant email should not cost 50 times more than a normal one. |
| Confidence check after the AI | A wrong ticket is worse than a ticket a human has to look at. |

---

## 4. Quick start (about 10 minutes)

### What you need

- A **Windows, Mac or Linux** computer
- **Python 3.12 or 3.13** (check with `python --version`)
  - ⚠️ **Avoid Python 3.15 for now.** Some libraries do not have ready-made packages for it yet, which causes confusing install errors.
- **Git** (only if you want to download the project with `git clone`)
- **VS Code** (recommended, but any editor works)
- **No AI account or API key is needed.** The project ships with a built-in "mock" AI so everything works offline.

### Step 1: Get the project

**Option A: with Git**
```powershell
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

**Option B: without Git**
On the GitHub page, click the green **Code** button, then **Download ZIP**. Unzip it and open the folder in VS Code.

### Step 2: Create a virtual environment

A virtual environment is a private box for this project's libraries, so they do not mix with other projects.

**Windows (PowerShell):**
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If PowerShell refuses to run the script, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You will know it worked when your prompt starts with `(.venv)`.

### Step 3: Install the libraries

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> 💡 Always write `python -m pip` and `python -m streamlit` (not just `pip` or `streamlit`). This guarantees that the commands use the Python inside your virtual environment.

### Step 4: Create the sample data

```powershell
python make_dataset.py
```
This creates `data/support_inbox.xlsx` (24 messy emails) and `data/expected_labels.csv` (the answer key). Skip this step if the `data/` folder already has these files.

### Step 5: Run it

```powershell
python main.py
```

You should see a score table with about **91% routing accuracy**, and a new file `output/tickets.xlsx`.

### Step 6: Open the dashboard

```powershell
python -m streamlit run app.py
```

Your browser opens at **http://localhost:8501**. Use the **Local URL** shown in the terminal. The "Network URL" is for other devices on your network, so do not share it.

To stop the app, press **Ctrl + C** in the terminal.

---

## 5. Using the Streamlit app

The dashboard has three tabs and a settings sidebar.

### Sidebar settings

| Setting | What it does |
|---|---|
| **Classifier** | **Mock** (offline, free, default) or **Real LLM** (needs a provider and API key) |
| **Confidence threshold** | Below this number (default 0.70) a message goes to Needs Review |
| **Token budget per run** | Total AI "reading" allowed per run. When it is used up, remaining messages go to Needs Review instead of the AI. |

### Tab 1: Try one message

Type a subject and message (or pick an example from the dropdown) and press **Route it**. You will see:

- which team it goes to, and the priority
- how confident the AI was
- how many tokens were used and how many private items were masked
- a plain-English **why**
- **"What the LLM actually saw"**: the text after masking and trimming. Use it to confirm that phone numbers and card numbers were hidden.
- a step-by-step **pipeline trace**

### Tab 2: Process inbox

Run the whole sample inbox, or upload your own Excel file. You get summary numbers, a chart of tickets per team, a filterable ticket table, a run log, a list of data problems found, an evaluation table (sample data only), and a **Download tickets.xlsx** button.

Your own Excel file needs exactly these columns: `ID`, `Received At`, `Customer Email`, `Subject`, `Message`.

### Tab 3: How it works

A one-page summary of the pipeline.

### Good messages to try

| Subject | Message | What you should see |
|---|---|---|
| URGENT!!! | I was charged twice for order 4540!! Card ending 4417. Call me on 9876543210 | Finance, High priority, 2 private items masked |
| Broken + bulk | My blender broke, and I also want a bulk quote for 50 more. | **Two tickets:** Sales and Product |
| Automatic reply: Out of office | I am out of office until Monday. | Spam Review, 0 tokens used (no AI call) |
| Hi | hmm what | Needs Review (not enough information) |

---

## 6. Using the command line

```powershell
python main.py
```

This runs the whole pipeline on the sample inbox, prints the scores, and writes **`output/tickets.xlsx`** with five sheets:

| Sheet | Contents |
|---|---|
| **Tickets** | The finished tickets: team, priority, summary, confidence, routing reason, status |
| **Run Log** | One row per email: tokens used, private items masked, errors |
| **Issues** | Emails set aside during cleaning (duplicates, empty messages) |
| **Evaluation** | Scores against the answer key |
| **Eval Detail** | Expected vs actual team for each email |

> If you get a `PermissionError` on `tickets.xlsx`, close the file in Excel and run it again.

---

## 7. Using the API

The same pipeline is available as a web service, so other programs can send emails to it.

```powershell
python -m uvicorn src.api:app --reload
```

Open **http://127.0.0.1:8000/docs** for an interactive page where you can try everything.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Returns `{"status": "ok"}` if the service is alive |
| `POST /route` | Route one message |
| `POST /route-batch` | Route up to 200 messages with one shared token budget |

**Example request** (PowerShell):
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/route `
  -ContentType "application/json" `
  -Body '{"subject":"Invoice","message":"Where can I download my invoice for order 4533?"}'
```

**Example response:**
```json
{
  "id": "1",
  "teams": ["Finance"],
  "reason": "llm",
  "priority": "Low",
  "summary": "Mock: invoice. where can i download my invoice for order 4533?",
  "confidence": 0.8,
  "tokens": 14,
  "pii_masked": 0
}
```

Messages longer than 5,000 characters are rejected. To require a password, set `ROUTER_API_KEY` and send it in an `X-API-Key` header.

---

## 8. Sending tickets by email (optional)

After tickets are created, each one can be emailed to its team. **This is optional.** The rest of the project works without it.

### How it works

- Each team has its own email address, set in a file called `.env`.
- Any team without its own address falls back to `DEFAULT_TEAM_EMAIL`.
- **Dry run is ON by default.** It builds every email but sends nothing, so you can check first.
- A ticket that was already emailed in the same session is skipped, so you never send duplicates.
- A failed email is retried once, then reported. It never stops the other emails.

### Setup

**1.** Copy `.env.example` to a new file named `.env` in the project root (next to `app.py`).

**2.** Edit `.env`:
```ini
DEFAULT_TEAM_EMAIL=someone@example.com
TEAM_EMAIL_SALES=sales@yourcompany.com
TEAM_EMAIL_FINANCE=finance@yourcompany.com
# ... one line per team (PRODUCT, IT, SUPPORT, NEEDS_REVIEW, SPAM_REVIEW)

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.address@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_DRY_RUN=1
```

**3. Gmail users:** Gmail does not accept your normal password for this. Turn on 2-Step Verification, then create an **App password** in your Google account security settings and paste it as `SMTP_PASSWORD`. Never share it.

**4.** Make sure `app.py` includes the email panel. Add this import near the top:
```python
from src.email_panel import render_email_panel
```
and this line in `tab_batch`, just above `st.download_button("Download tickets.xlsx", ...)`:
```python
    render_email_panel(b["tickets"])
```

**5.** Restart Streamlit (the `.env` file is read at startup), run the pipeline, open **📧 Email tickets to teams**, untick **Dry run**, and press **Send ticket emails**.

> ⚠️ Tickets contain the customer's original message. Test with the sample data only. Use company mailboxes before using real customer data.

---

## 9. Using a real AI model instead of the mock (optional)

By default the project uses a **mock classifier**: a simple keyword matcher that works offline. It is good for learning and testing, but it is not a real AI.

To use a real model:

**1. Install the package for your provider** (one of these):
```powershell
python -m pip install langchain-openai
python -m pip install langchain-google-genai
python -m pip install langchain-groq
```

**2. In the Streamlit sidebar:** choose **Real LLM (hosted)**, pick the provider, and paste your API key.

**Or from the command line** (PowerShell):
```powershell
$env:USE_MOCK = "0"
$env:LLM_PROVIDER = "openai"        # openai | azure | gemini | groq
$env:OPENAI_API_KEY = "sk-..."
python main.py
```

| Provider | Key variable | Default model |
|---|---|---|
| openai | `OPENAI_API_KEY` | gpt-4o-mini |
| gemini | `GOOGLE_API_KEY` | gemini-2.0-flash |
| groq | `GROQ_API_KEY` | llama-3.1-8b-instant |
| azure | Azure settings plus `AZURE_OPENAI_DEPLOYMENT` | your deployment |

> ⚠️ **Privacy warning:** in real mode, the **masked** customer text is sent to an outside company. Phone numbers, emails and card numbers are hidden first, but **names and addresses are not masked**. Get approval from your IT or security team before using real customer data.
>
> ⚠️ The real-provider path has not been tested against a live service. If you hit an error, check your key, your package install and your model name first.

---

## 10. Project structure: what every file does

```
ai-support-ticket-router/
│
├── app.py                  ← The Streamlit dashboard (what you click on)
├── main.py                 ← Runs everything from the command line
├── make_dataset.py         ← Creates the fake sample inbox and answer key
├── requirements.txt        ← The list of libraries to install
├── Dockerfile              ← Recipe for running the API in a container
├── .env.example            ← Template for your private settings (copy to .env)
├── .gitignore              ← Tells Git which files to never upload
├── README.md               ← This file
│
├── data/
│   ├── support_inbox.xlsx      ← 24 messy sample emails (fake data)
│   └── expected_labels.csv     ← The correct answers, used only for scoring
│
├── src/                    ← The actual logic, one file per job
│   ├── config.py               ← Settings: teams, thresholds, email addresses
│   ├── load_clean.py           ← Step ①: read Excel, tidy, deduplicate
│   ├── rules.py                ← Step ②: free rules that catch obvious spam
│   ├── pii.py                  ← Step ③: hide private data
│   ├── token_guard.py          ← Step ④: trim long text, enforce the budget
│   ├── schemas.py              ← The strict answer format the AI must follow
│   ├── llm_classifier.py       ← Step ⑤: the AI call, with retries and fallback
│   ├── pipeline.py             ← Connects all steps; makes the routing decision
│   ├── tickets.py              ← Step ⑦: builds tickets and the Excel file
│   ├── evaluate.py             ← Scores the results against the answer key
│   ├── api.py                  ← The web API (FastAPI)
│   ├── notifier.py             ← Sends tickets by email (optional)
│   └── email_panel.py          ← The email section of the dashboard (optional)
│
├── tests/                  ← Automatic checks that the code works
│   ├── test_all.py             ← Cleaning, rules, PII, token guard, pipeline, API
│   ├── test_app.py             ← The Streamlit dashboard
│   └── test_notifier.py        ← Email sending (uses a fake mail server)
│
└── output/                 ← Created when you run it. Contains tickets.xlsx
```

### What each source file does, in more detail

| File | Plain-English explanation |
|---|---|
| `config.py` | The control panel. It lists the teams, which category goes to which team, the confidence threshold (0.70), and reads email settings from `.env`. Change a value here instead of hunting through the code. |
| `load_clean.py` | Reads the Excel file as plain text, so order numbers are not turned into decimals. Trims spaces, lowercases emails, joins subject and message, and removes duplicates (same customer plus same message). **Empty messages are kept and flagged, never dropped.** |
| `rules.py` | A short list of patterns for things that are obviously junk: "out of office", "you have won", job applications, SEO offers. It returns the rule name, so you can always see why something was called spam. It is deliberately strict, because a wrong rule is worse than no rule. |
| `pii.py` | PII means "personally identifiable information". It swaps phone numbers, email addresses and card numbers for placeholders like `[PHONE]`. Order numbers are kept because the teams need them. |
| `token_guard.py` | A token is roughly a word-piece the AI reads and charges for. This file removes quoted replies and signatures, trims long emails (keeping the **end**, where the real question usually is), and stops sending to the AI once the run budget is used up. |
| `schemas.py` | The strict form the AI must fill in: 1 or 2 categories from a fixed list, a priority, a summary of at most 160 characters, and a confidence from 0 to 1. Anything else is rejected. |
| `llm_classifier.py` | Sends the masked text to the AI with clear instructions, validates the reply, retries with growing waits if it fails, and returns an error instead of crashing if it keeps failing. Includes the offline **mock** classifier. |
| `pipeline.py` | The conductor. For each message it runs steps ① to ⑥ and decides the final team(s). The dashboard, the command line and the API all use this same function, so they always agree. |
| `tickets.py` | Turns routing results into ticket rows (`TKT-0001`, ...) and writes a formatted Excel workbook. |
| `evaluate.py` | Compares the results with `expected_labels.csv` and reports accuracy, how many went to Needs Review, how many AI calls were made, and whether any private data reached the AI. |
| `api.py` | A small web service with `/health`, `/route` and `/route-batch`, with input size limits and an optional password. |
| `notifier.py` | Builds and sends one email per ticket, with dry run, retries and duplicate protection. |
| `email_panel.py` | The dashboard section that shows team email addresses and a Send button. |

---

## 11. The sample data

`make_dataset.py` creates 24 fake emails that copy the problems the customer described. **Nothing in it is real customer data.**

| What is in it | Examples (IDs) |
|---|---|
| Normal requests for each team | Bulk discount (1), blender broken (2), invoice (3), laptop RAM (4), store hours (8) |
| Private data | Phone number and card digits (5), phone number (16) |
| Junk | SEO offer (9), job application (10), out-of-office (11), lottery (24) |
| A wrong-company email | "Where is my Amazon parcel?" (12) |
| Two requests in one email | Broken blender **and** bulk quote (13) |
| Mixed Hindi and English | "mera order abhi tak nahi aaya..." (14) |
| Duplicates | Same email sent twice (15, 21) |
| A very long, rambling email | The real question is in the last line (17) |
| Empty message | Only a subject, no body (22) |
| Typos | "pls help my ordr not here" (23) |

Results on the sample, using the **mock** classifier:

| Measure | Result |
|---|---|
| Routing accuracy | about 91% (target: 90% or more) |
| Confidently wrong | 0 |
| Sent to Needs Review | about 14% |
| Private data reaching the AI | 0 |

> ⚠️ These numbers come from the **mock** keyword matcher. They say nothing about how a real AI model would perform. Run the pipeline with a real model and compare.

---

## 12. How a message is routed

| Situation | Where it goes | AI called? |
|---|---|---|
| Empty message | Needs Review | No |
| A rule matches (out-of-office, lottery, job application, SEO) | Spam Review | No |
| The token budget has been used up | Needs Review | No |
| The AI call failed after retries | Needs Review | Yes (it failed) |
| AI confidence is below 0.70, or the AI says "Unclear" | Needs Review | Yes |
| AI is confident, one request | That team | Yes |
| AI is confident, two requests | Two tickets, two teams | Yes |

### Categories and teams

| AI category | Team that gets the ticket |
|---|---|
| Sales | Sales |
| Product | Product |
| Billing | Finance |
| IT | IT |
| General | Support |
| Spam | Spam Review |
| Unclear | Needs Review |

### Priorities

| Priority | When |
|---|---|
| **High** | Double charge, website down, an angry customer |
| **Medium** | Product defects, quote requests, refunds |
| **Low** | General questions |

---

## 13. Safety features

| Feature | How it protects you |
|---|---|
| **Nothing is auto-deleted** | Junk goes to Spam Review so a human can check it. A real customer is never silently lost. |
| **Private data is masked first** | The AI only sees `[PHONE]`, `[EMAIL]`, `[CARD]`. The original message stays inside the ticket for the team. |
| **Strict AI answers** | The AI's reply must match the exact format. Invented categories or out-of-range confidence are rejected. |
| **Prompt-injection defence** | The AI is told that the customer's message is data, not instructions. A message saying "ignore all instructions" should not be obeyed. |
| **Cost control** | Rules skip the AI, long emails are trimmed, replies are capped, and there is a per-run token budget. |
| **Retries with backoff** | A temporary network problem does not lose a message. The waits get longer each time (1 s, 2 s, 4 s). |
| **Human fallback** | Low confidence, an unclear message, a failed call or an exhausted budget all lead to Needs Review. |
| **No duplicate emails** | Each ticket is emailed once per session. |
| **Secrets stay private** | `.env` is excluded from Git, so passwords are never uploaded. |

---

## 14. Settings reference

Settings live in `src/config.py` and in a `.env` file (copy `.env.example` to `.env`). **Never upload `.env` to GitHub.**

| Setting | Default | Meaning |
|---|---|---|
| `USE_MOCK` | `1` | `1` = offline mock AI, `0` = real AI provider |
| `LLM_PROVIDER` | `openai` | `openai`, `azure`, `gemini` or `groq` |
| `LLM_MODEL` | provider default | Model name |
| `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY` | none | Your provider key |
| `ROUTER_API_KEY` | none | If set, API callers must send it as `X-API-Key` |
| `DEFAULT_TEAM_EMAIL` | none | Fallback address for any team without its own |
| `TEAM_EMAIL_<TEAM>` | none | For example `TEAM_EMAIL_FINANCE`, `TEAM_EMAIL_NEEDS_REVIEW` |
| `SMTP_HOST`, `SMTP_PORT` | `smtp.gmail.com`, `587` | Mail server |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | none | Sending account (use an app password) |
| `SMTP_USE_SSL` | `0` | `1` for port 465 |
| `EMAIL_DRY_RUN` | `1` | `1` = build emails but send nothing |

Values you can change in code:

| Where | Setting | Default |
|---|---|---|
| `config.py` | `CONFIDENCE_THRESHOLD` | 0.7 |
| `token_guard.py` | `MAX_INPUT_TOKENS` | 120 (small for the demo; use about 500 in production) |
| `token_guard.py` | `MAX_OUTPUT_TOKENS` | 150 |
| `token_guard.py` | `RUN_BUDGET_TOKENS` | 1000 (the dashboard slider overrides it) |

---

## 15. Running the tests

```powershell
python -m pytest -q tests
```

| Test file | What it checks |
|---|---|
| `test_all.py` | Cleaning, spam rules (and that real customers are never caught), private-data masking, token trimming and budget, every routing decision, AI output validation, the API |
| `test_app.py` | The dashboard: loading, routing a message, the batch run, the upload error |
| `test_notifier.py` | Email routing to the right team, dry run, retry, no duplicates, missing settings |

All emails in tests go to a **fake mail server**. Nothing is really sent.

---

## 16. Docker (optional)

The Dockerfile runs the **API** (not the dashboard) in a container using the mock classifier.

```powershell
docker build -t ticket-router .
docker run -p 8000:8000 ticket-router
```

Then open http://localhost:8000/docs. This Dockerfile has not been tested in this project.

---

## 17. Troubleshooting

| Problem | What to do |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Run commands from the project root, the folder that contains `main.py`. |
| `ModuleNotFoundError: No module named 'fastapi'` (or `streamlit`) | The virtual environment is not active, or packages were not installed. Activate it and run `python -m pip install -r requirements.txt`. |
| Packages go to the wrong place | Always use `python -m pip` and `python -m streamlit`. |
| `ModuleNotFoundError: No module named 'langchain_openai'` | You chose **Real LLM**. Either switch back to **Mock**, or run `python -m pip install langchain-openai`. |
| `Microsoft Visual C++ 14.0 or greater is required` during install | You are on a very new Python (such as 3.15). Create a new virtual environment with Python 3.12 or 3.13. |
| `Could not convert '23%' with type str` (Arrow error) | In `app.py`, change the evaluation table line to `st.dataframe(b["summary"].astype(str), hide_index=True, width="stretch")`. |
| `pyarrow requires NumPy 2.0 or newer` | Run `python -m pip install -U numpy pyarrow`. |
| `PermissionError` on `tickets.xlsx` | Close the file in Excel and run again. |
| `KeyError` during evaluation | Your `expected_labels.csv` is out of date. Re-run `python make_dataset.py`. |
| `'git' is not recognized` | Install Git (`winget install --id Git.Git -e`), then fully close and reopen VS Code. |
| `Repository not found` when pushing | Check the repo exists on GitHub, the username and repo name are exact, and the browser sign-in used the right account. |
| Gmail refuses to send (authentication error) | Use an **App password**, not your normal password, and make sure 2-Step Verification is on. |
| Email panel says settings are missing | Fill in `SMTP_USER` and `SMTP_PASSWORD` in `.env`, then restart Streamlit. |
| Changes to `.env` are ignored | Stop and restart Streamlit or the API. `.env` is read at startup. |
| PowerShell shows hundreds of red errors after you paste code | The code went into the terminal. Python code belongs in a file in the editor. Only commands go in the terminal. |

---

## 18. Honest limits of this project

This is a learning project. Please read these before relying on it.

| Limit | Details |
|---|---|
| **Names and addresses are not masked** | Regular expressions cannot reliably find names. A proper fix needs a named-entity-recognition (NER) model. |
| **Private-data patterns are limited** | The masker knows Indian-style phone numbers, email addresses and card patterns. Other formats may slip through, so keep testing it with your own examples. |
| **The mock is not an AI** | The 91% score comes from a keyword matcher. A real model must be measured separately. |
| **Real LLM mode is untested against a live service** | The code is written and structured for it, but your first real run is the actual test. |
| **No Freshdesk or helpdesk integration** | Tickets are written to Excel (and optionally emailed). They are not created in a real ticketing system. |
| **No Hindi-specific handling** | Mixed Hindi and English works only as far as the model understands it. |
| **No database, login or user accounts** | Everything runs in memory and in files. |
| **The email-sent memory resets** | Duplicate protection lasts for the session only. Restarting the app forgets what was sent. |
| **Token counting is an estimate** | It assumes about 4 characters per token. Hindi and mixed text use more tokens than this estimate suggests. |
| **Signature stripping is simple** | A customer who writes "regards," in the middle of a message could lose the text after it. |
| **Docker is untested** | The Dockerfile has not been run. |

---

## 19. Ideas for next steps

1. **Try a real AI model** and compare its accuracy with the mock.
2. **Create tickets in Freshdesk** (or Jira, ServiceNow) through their API instead of Excel.
3. **Add a name and address masker** using an NER model.
4. **Add Hindi support** and test with more mixed-language messages.
5. **Add a database** so tickets and "already emailed" status survive restarts.
6. **Add login** to the dashboard and the API.
7. **Build a larger test set** (100 or more labelled messages) for more trustworthy accuracy numbers.
8. **Watch costs and quality over time** with proper logging and tracing.

---

## 20. Glossary

| Term | Meaning |
|---|---|
| **FDE (Forward Deployed Engineer)** | An engineer who works directly with a customer to build and deploy software for their real problem |
| **LLM** | Large Language Model, the kind of AI behind chatbots |
| **Classifier** | Something that puts an item into a category |
| **Mock** | A stand-in used for testing instead of the real thing |
| **PII** | Personally identifiable information: phone numbers, emails, card numbers, and so on |
| **Masking** | Replacing private data with a placeholder such as `[PHONE]` |
| **Token** | A small piece of text the AI reads and charges for, roughly a word-piece |
| **Token budget** | A cap on how much text may be sent to the AI in one run |
| **Confidence** | The AI's own estimate (0 to 1) of how sure it is |
| **Threshold** | The cut-off number. Below it, a human decides. |
| **Guardrail** | A safety check around the AI |
| **Handoff** | Passing a case to a human |
| **Idempotent** | Safe to repeat. Doing it twice has the same effect as doing it once. |
| **Retry with backoff** | Trying again after a growing wait, such as 1, 2, then 4 seconds |
| **Pydantic** | A Python library that checks data has the right shape |
| **Streamlit** | A Python library for building simple web dashboards |
| **FastAPI** | A Python library for building web APIs |
| **API** | A way for one program to talk to another over the web |
| **SMTP** | The standard system for sending email |
| **Virtual environment** | A private folder of libraries for one project |
| **Dry run** | A practice run that does everything except the final real action |

---

## License and data

This is a personal learning project. All sample data is fake. Add a license of your choice (for example MIT) before sharing it publicly.
