"""Deploy phase: expose the pipeline as an HTTP service.
Run:  uvicorn src.api:app --reload      Docs: http://127.0.0.1:8000/docs"""
import os, re
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from src.pipeline import process_message, get_classifier
from src.token_guard import TokenBudget

app = FastAPI(title="Northwind Ticket Router", version="1.0")
_classifier = get_classifier()
API_KEY = os.getenv("ROUTER_API_KEY")   # if set, callers must send header X-API-Key


class Query(BaseModel):
    id: Optional[str] = "1"
    customer_email: str = ""
    subject: str = ""
    message: str = Field(max_length=5000)   # input validation: reject absurdly large bodies


class RouteResponse(BaseModel):
    id: str
    teams: List[str]
    reason: str
    priority: str
    summary: str
    confidence: Optional[float]
    tokens: int
    pii_masked: int


def _check_key(key):
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid API key")


def _route(q: Query, budget: TokenBudget) -> RouteResponse:
    subject = re.sub(r"\s+", " ", q.subject).strip()
    message = re.sub(r"\s+", " ", q.message).strip()
    text = f"{subject}. {message}".strip(" .")
    r = process_message(q.id, text, is_empty=(message == ""), classifier=_classifier, budget=budget)
    return RouteResponse(id=r["id"], teams=r["teams"], reason=r["reason"], priority=r["priority"],
                         summary=r["summary"], confidence=r["confidence"], tokens=r["tokens"],
                         pii_masked=sum(r["pii_counts"].values()))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/route", response_model=RouteResponse)
def route(q: Query, x_api_key: Optional[str] = Header(default=None)):
    _check_key(x_api_key)
    return _route(q, TokenBudget())


@app.post("/route-batch", response_model=List[RouteResponse])
def route_batch(items: List[Query], x_api_key: Optional[str] = Header(default=None)):
    _check_key(x_api_key)
    if len(items) > 200:
        raise HTTPException(status_code=413, detail="max 200 messages per batch")
    budget = TokenBudget()           # one shared budget for the whole batch
    return [_route(q, budget) for q in items]
