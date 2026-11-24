# Northwind Ticket Router (FDE practice project)

Excel inbox -> clean -> rules -> mask PII -> token guard -> LLM -> confidence check -> tickets.

## Run (Windows PowerShell)
    python -m venv venv ; .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python make_dataset.py          # regenerates data/
    python main.py                  # writes output/tickets.xlsx + prints evaluation
    python -m pytest -q tests
    uvicorn src.api:app --reload    # http://127.0.0.1:8000/docs

## Real LLM instead of the mock
    pip install langchain-openai
    $env:USE_MOCK = "0"; $env:LLM_PROVIDER = "openai"; $env:OPENAI_API_KEY = "sk-..."
    python main.py
(providers: openai | azure | gemini | groq)

## Docker
    docker build -t ticket-router . ; docker run -p 8000:8000 ticket-router
